There are many treatments available for wet macular degeneration of the type “Anti-VEGF”. Each treatment may be used in different “Protocols”. These are examples of protocols but many others have been and may be used: 
## 1. Eylea protocol: induction and maintenance
    1. Give one Eylea injection to the affected eye every month for 3 months (3 injections)
    2. Check the treatment has worked (defined as vision no worse than baseline, retinal thickness improved)
        1. If the treatment has worked, continue treating every 2 months indefinitely 
        2. If the treatment does not work, stop or consider switching
    3. At any time in treatment, if the vision has fallen by more than 15 ETDRS letters from baseline without another reason (eg cataract) then consider stopping treatment
## 2. Eylea protocol: treat and extend
    1. Give one Eylea injection to the affected eye every month for 3 months (3 injections)
    2. Check the treatment has worked (defined as vision no worse than baseline, retinal thickness improved)
        1. If the treatment has worked, extend interval to 2 months
        2. After interval check patient:
            1. If disease recurring, treat and check at new_interval = (interval -2 weeks)
            2. If disease not recurring, treat and check in new_interval = (interval + 2 weeks)
            3. Loop with interval now set to new_interval
        3. If the treatment does not work, stop or consider switching
    3. At any time in treatment, if the vision has fallen by more than 15 ETDRS letters from baseline without another reason (eg cataract) then consider stopping treatment



## 3. Eylea protocol: treat and extend Veeramani


### Initial Variables
- Treatment: "Eylea"
- Monitoring: "OCT" (Optical Coherence Tomography)
- Total Injections: 15
- Duration: 3 years
- Base Unit: weeks

### Year 1 Schedule (Injections 1-7)
1. Injection #1
   - Timing: Within 1 week of start
   - OCT: No

2. Injection #2
   - Interval: 4 weeks from #1
   - OCT: No

3. Injection #3
   - Interval: 4 weeks from #2
   - OCT: No

4. Injection #4
   - Interval: 8 weeks from #3
   - OCT: Yes

5. Injection #5
   - Interval: 8 weeks from #4
   - OCT: No

6. Injection #6
   - Interval: 8 weeks from #5
   - OCT: No

7. Injection #7
   - Interval: 8 weeks from #6
   - OCT: Yes

### Year 2-3 Schedule (Injections 8-15)
8. Injection #8
   - Interval: 10 weeks from #7
   - OCT: No

9. Injection #9
   - Interval: 10 weeks from #8
   - OCT: Yes

10. Injection #10
    - Interval: 12 weeks from #9
    - OCT: No

11. Injection #11
    - Interval: 12 weeks from #10
    - OCT: Yes

12. Injection #12
    - Interval: 14 weeks from #11
    - OCT: No

13. Injection #13
    - Interval: 14 weeks from #12
    - OCT: Yes

14. Injection #14
    - Interval: 16 weeks from #13
    - OCT: No

15. Injection #15
    - Interval: 16 weeks from #14
    - OCT: Yes

### Exception Rule
- Condition: If fluid detected during OCT review
- Action: 
  1. Return to previous interval length
  2. Schedule OCT for next injection



These are just protocols for 1 agent: many different agents, doses, and protocols are possible. 

 For a visit there can be several options:

Visit measures vision
As above + OCT image taken
Visit measures vision and injection done
As above + OCT taken

Each of those visit types may or may not be accompanied by a decision process, ie a doctor looks at the situation and makes a decision. Every visit should be associated with a nurse decision, ie nurse notes if vision has fallen by more than 15 letters and escalates to doctor decision. 


We would like to develop a representation of the treatment protocols in a format that is human and machine readable, ie it can easily be parsed in python to populate a simulation model, but it can also be understood by a human reader with minimum of training. 

This will form the basis of information storage and representation for a DES discrete event simulation model written in python, and also for an ABS agent based simulation also in python. The simulations should be arranged so it is possible to run them together and compare outputs if needed. 

Please proceed step by step and record any important design decisions in files in meta; once there is a basic model working we will add a testing framework and thereafter will use test driven design to take the project forward. 

Please keep an up-to-date file of next_steps.md in the meta folder.
Please keep an up-to-date file of issues.md in the meta folder.
Please keep and up-to-date file of design_decisions.md in the meta folder.
Please keep an up-to-date file of references.md in the meta folder.
Please keep an up-to-date file of files_in_use.md in the meta folder.

Please keep all files in the meta folder unless they are code or YAML 
files.