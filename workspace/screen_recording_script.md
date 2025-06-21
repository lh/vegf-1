# Screen Recording Script for NAMD Simulation Demo
## Duration: 2.5 minutes (slides 6:00-8:30)

---

## INTRO (0:00-0:10)
**ACTION:** Show application home page
**SCRIPT:** "Let me show you how our agent-based simulation works in practice. This is our Streamlit application with four main modules."

**ACTION:** Hover over each sidebar option briefly
**SCRIPT:** "We have protocol management, simulation engine, analysis tools, and comparison capabilities."

---

## PROTOCOL MANAGEMENT (0:10-0:30)
**ACTION:** Click on "Protocol Editor" in sidebar
**SCRIPT:** "First, let's load a real NHS treatment protocol. These protocols define how we treat patients with anti-VEGF therapy."

**ACTION:** Select "NHS Aflibercept TAE v1.0" from dropdown
**SCRIPT:** "This is based on actual NHS prescribing patterns - notice the treat-and-extend intervals go from 7 to 20 weeks."

**ACTION:** Briefly scroll through protocol parameters
**SCRIPT:** "The protocol includes vision distributions, discontinuation rates, and treatment response patterns - all calibrated from real-world data."

---

## RUNNING SIMULATION (0:30-1:00)
**ACTION:** Navigate to "Run Simulation"
**SCRIPT:** "Now let's simulate 1000 patients over 5 years to see what happens in practice."

**ACTION:** Set parameters:
- Patients: 1000
- Duration: 5 years
- Random seed: 2024
**SCRIPT:** "We'll run 1000 patients - each an independent agent with their own characteristics and treatment journey."

**ACTION:** Click "Run Simulation" button
**SCRIPT:** "The simulation tracks each patient individually - their vision changes, treatment decisions, and discontinuation events."

**ACTION:** Show progress bar completing
**SCRIPT:** "In seconds, we've simulated 5 years of treatment for 1000 patients - something impossible with simple spreadsheet models."

---

## PATIENT EXPLORER (1:00-1:30)
**ACTION:** Click "Patient Explorer" in sidebar
**SCRIPT:** "Let's look at individual patient journeys to understand what's happening."

**ACTION:** Select a patient who discontinued early
**SCRIPT:** "Here's a patient who discontinued after 18 months due to treatment failure - their vision dropped below the futility threshold."

**ACTION:** Show the timeline visualization
**SCRIPT:** "You can see each injection, the vision trajectory, and exactly when and why they stopped treatment."

**ACTION:** Select a successful patient
**SCRIPT:** "Compare this to a patient who responded well - they extended to 16-week intervals and maintained stable vision."

**ACTION:** Point to discontinuation statistics
**SCRIPT:** "Overall, we see realistic dropout - only 55% still on treatment at year 5, matching NHS experience."

---

## POPULATION ANALYSIS (1:30-2:00)
**ACTION:** Navigate to "Calendar-Time Analysis"
**SCRIPT:** "Now let's examine the population-level patterns that emerge from these individual journeys."

**ACTION:** Show the streamgraph visualization
**SCRIPT:** "This shows how our patient population evolves over time - active treatment, various reasons for discontinuation, and the growing burden of treatment failures."

**ACTION:** Point to the treatment burden graph
**SCRIPT:** "Notice how injection frequency decreases over time as stable patients extend intervals - but the most severely affected patients still need frequent treatment."

**ACTION:** Scroll to show outcome distributions
**SCRIPT:** "We can see the full distribution of outcomes - not just averages. Some patients do very well, others poorly, just like real life."

---

## PROTOCOL COMPARISON (2:00-2:20)
**ACTION:** Briefly navigate to "Compare Protocols"
**SCRIPT:** "Finally, we can compare different treatment strategies side-by-side."

**ACTION:** Show comparison visualization
**SCRIPT:** "This helps answer critical questions: Is extending to 20 weeks safe? Should we switch non-responders earlier? What's the real impact on NHS capacity?"

---

## CONCLUSION (2:20-2:30)
**ACTION:** Return to home page
**SCRIPT:** "In just minutes, we've modeled complex treatment pathways that would take months to analyze in clinic. This tool transforms how we think about optimizing AMD treatment in the NHS."

**ACTION:** Hold on home page
**SCRIPT:** "Now let's return to see what insights this approach provides..."

---

## DIRECTOR'S NOTES:

### Key Points to Emphasize Visually:
1. **Individual variation** - Show different patient trajectories
2. **Real-world messiness** - Point out treatment gaps, delays
3. **Emergence** - Population patterns arising from individual behaviors
4. **Speed** - Emphasize how quickly we can test scenarios

### Avoid:
1. Getting lost in technical details
2. Showing too many menu options
3. Dwelling on any one screen too long
4. Showing error messages or glitches

### Backup Plan:
- Have pre-loaded simulation results ready
- Know which patient IDs show good examples
- Practice the exact click sequence beforehand
- Have screenshots ready if live demo fails

### Visual Tips:
- Use mouse to point at key features
- Pause on important numbers
- Keep movements smooth and deliberate
- Ensure text is readable in recording