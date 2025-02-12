import logging
from datetime import datetime, timedelta
from simulation.des import DiscreteEventSimulation
from simulation.config import SimulationConfig
from protocol_models import (
    TreatmentProtocol, ProtocolPhase, PhaseType, VisitType, 
    ActionType, DecisionType, LoadingPhase
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("des_queue_test")

class QueueDebugSimulation(DiscreteEventSimulation):
    def __init__(self, config):
        super().__init__(config)
        # Track queue metrics
        self.queue_metrics = {
            "max_queue_length": 0,
            "queue_adds": 0,
            "queue_removes": 0,
            "resource_allocations": 0,
            "resource_releases": 0,
            "rescheduled_visits": 0,
            "event_delays": []  # Track time between scheduled and actual execution
        }
    
    def _request_resources(self, event):
        """Override to add detailed logging"""
        logger.debug(f"\nAttempting to allocate resources for {event.patient_id} at {event.time}")
        logger.debug(f"Current queue lengths: {self._get_queue_lengths()}")
        logger.debug(f"Current utilization: {dict(self.global_stats['resource_utilization'])}")
        
        needed_resources = {
            "nurses": 1,
            "oct_machines": 1 if "oct_scan" in event.data.get("actions", []) else 0,
            "doctors": 1 if "injection" in event.data.get("actions", []) else 0
        }
        logger.debug(f"Needed resources: {needed_resources}")
        
        # Check if we have enough capacity
        for resource, needed in needed_resources.items():
            if needed > 0:
                current = self.global_stats["resource_utilization"][resource]
                capacity = self.resource_capacity[resource]
                available = capacity - current
                logger.debug(f"{resource}: need {needed}, have {available} available ({current}/{capacity} in use)")
                
                if available < needed:
                    # Not enough resources, add to queue if space
                    if len(self.resource_queue[resource]) < self.global_stats["queue_stats"]["max_queue_length"]:
                        if event not in self.resource_queue[resource]:
                            logger.debug(f"Adding to {resource} queue (length: {len(self.resource_queue[resource])})")
                            self.resource_queue[resource].append(event)
                            self.queue_metrics["queue_adds"] += 1
                    else:
                        logger.debug(f"{resource} queue full, rescheduling visit")
                        self.global_stats["queue_stats"]["queue_full_events"] += 1
                        self.queue_metrics["rescheduled_visits"] += 1
                        self._reschedule_visit(event)
                    return False
        
        # If we get here, we have enough of all resources
        logger.debug("Resources available, allocating...")
        for resource, needed in needed_resources.items():
            if needed > 0:
                self.global_stats["resource_utilization"][resource] += needed
                self.queue_metrics["resource_allocations"] += 1
        
        return True

    def _handle_resource_release(self, event):
        """Override to add detailed logging"""
        logger.debug(f"\nReleasing resources at {event.time}")
        logger.debug(f"Resources being released: {event.data['resources']}")
        logger.debug(f"Queue state before release: {self._get_queue_lengths()}")
        
        # Release all resources used by this patient
        for resource in event.data["resources"]:
            if self.global_stats["resource_utilization"][resource] > 0:
                self.global_stats["resource_utilization"][resource] -= 1
                self.queue_metrics["resource_releases"] += 1
        
        logger.debug(f"Resource utilization after release: {dict(self.global_stats['resource_utilization'])}")
        
        # Try to process queued events
        processed = set()
        for resource_type in ["doctors", "nurses", "oct_machines"]:
            if self.resource_queue[resource_type]:
                logger.debug(f"Processing {resource_type} queue (length: {len(self.resource_queue[resource_type])})")
                for queued_event in list(self.resource_queue[resource_type]):
                    if queued_event not in processed:
                        if self._request_resources(queued_event):
                            # Successfully allocated resources, remove from all queues
                            for r in ["doctors", "nurses", "oct_machines"]:
                                if queued_event in self.resource_queue[r]:
                                    self.resource_queue[r].remove(queued_event)
                                    self.queue_metrics["queue_removes"] += 1
                            processed.add(queued_event)
                            
                            # Track delay
                            delay = (self.clock.current_time - queued_event.time).total_seconds() / 60
                            self.queue_metrics["event_delays"].append(delay)
                            logger.debug(f"Processing queued event with {delay} minute delay")
                            
                            self._handle_visit(queued_event)
        
        logger.debug(f"Queue state after processing: {self._get_queue_lengths()}")

    def _get_queue_lengths(self):
        """Helper to get current queue lengths"""
        return {r: len(q) for r, q in self.resource_queue.items()}

def create_test_protocol():
    """Create a minimal protocol for testing"""
    visit_type = VisitType(
        name="test_visit",
        duration_minutes=30,
        required_actions=[ActionType.VISION_TEST, ActionType.OCT_SCAN, ActionType.INJECTION],
        optional_actions=[],
        decisions=[DecisionType.NURSE_CHECK]
    )
    
    phase = LoadingPhase(
        phase_type=PhaseType.LOADING,
        duration_weeks=12,
        visit_interval_weeks=4,
        required_treatments=3,
        visit_type=visit_type,
        min_interval_weeks=4,
        max_interval_weeks=12,
        interval_adjustment_weeks=2
    )
    
    protocol = TreatmentProtocol(
        agent="test",
        protocol_name="test_protocol",
        version="1.0",
        description="Test protocol",
        phases={"loading": phase},
        parameters={},
        discontinuation_criteria=[]
    )
    
    return protocol

def run_queue_test():
    """Run simulation with detailed queue debugging"""
    # Initialize minimal config
    config = SimulationConfig(
        parameters={
            "vision": {
                "baseline_mean": 65,
                "measurement_noise_sd": 2,
                "max_letters": 85,
                "min_letters": 0,
                "headroom_factor": 0.8
            },
            "treatment_response": {
                "loading_phase": {
                    "vision_improvement_mean": 5,
                    "vision_improvement_sd": 2,
                    "improve_probability": 0.7,
                    "stable_probability": 0.2,
                    "decline_probability": 0.1
                }
            },
            "resources": {
                "doctors": 5,
                "nurses": 5,
                "oct_machines": 5
            }
        },
        protocol=create_test_protocol(),
        simulation_type="discrete_event",
        num_patients=2,    # Minimal patient load
        duration_days=30,  # Just test 1 month
        random_seed=42,
        verbose=True,
        start_date=datetime(2023, 1, 1)
    )
    
    logger.info("Starting queue debug simulation")
    sim = QueueDebugSimulation(config)
    
    # Set simulation end date first
    end_date = config.start_date + timedelta(days=config.duration_days)
    sim.clock.end_date = end_date
    
    # Then register protocol and add test patients
    protocol = create_test_protocol()
    sim.register_protocol("test_protocol", protocol)
    sim.add_patient("TEST001", "test_protocol")
    sim.add_patient("TEST002", "test_protocol")
    
    logger.info("\nRunning simulation...")
    event_count = 0
    max_events = 100000  # Safety limit to prevent infinite loops
    
    while sim.clock.current_time < end_date and event_count < max_events:
        event_count += 1
        if event_count % 100 == 0:
            logger.info(f"Processed {event_count} events...")
            
        event = sim.clock.get_next_event()
        if not event:
            logger.info("No more events to process")
            break
            
        # If event is beyond end date, stop processing
        if event.time > end_date:
            logger.info("Reached end date")
            break
        
        logger.debug(f"\nProcessing event: {event.event_type} for {event.patient_id}")
        logger.debug(f"Time: {event.time}")
        logger.debug(f"Queue state before processing:")
        for resource, queue in sim.resource_queue.items():
            logger.debug(f"  {resource}: {len(queue)} events")
        
        sim.process_event(event)
        
        # Update max queue length
        current_max = max(len(q) for q in sim.resource_queue.values())
        sim.queue_metrics["max_queue_length"] = max(
            sim.queue_metrics["max_queue_length"],
            current_max
        )
        
        logger.debug(f"Queue state after processing:")
        for resource, queue in sim.resource_queue.items():
            logger.debug(f"  {resource}: {len(queue)} events")
    
    # Print final metrics
    logger.info("\nSimulation complete. Final metrics:")
    logger.info(f"Max queue length: {sim.queue_metrics['max_queue_length']}")
    logger.info(f"Queue additions: {sim.queue_metrics['queue_adds']}")
    logger.info(f"Queue removals: {sim.queue_metrics['queue_removes']}")
    logger.info(f"Resource allocations: {sim.queue_metrics['resource_allocations']}")
    logger.info(f"Resource releases: {sim.queue_metrics['resource_releases']}")
    logger.info(f"Rescheduled visits: {sim.queue_metrics['rescheduled_visits']}")
    
    if sim.queue_metrics['event_delays']:
        avg_delay = sum(sim.queue_metrics['event_delays']) / len(sim.queue_metrics['event_delays'])
        max_delay = max(sim.queue_metrics['event_delays'])
        logger.info(f"Average event delay: {avg_delay:.1f} minutes")
        logger.info(f"Maximum event delay: {max_delay:.1f} minutes")

if __name__ == "__main__":
    run_queue_test()
