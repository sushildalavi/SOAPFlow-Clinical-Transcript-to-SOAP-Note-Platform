from fastapi import APIRouter, Query
from app.schemas.response import DemoTranscriptResponse

router = APIRouter()

DEMO_TRANSCRIPTS = [
    DemoTranscriptResponse(
        title="Hypertension Follow-Up",
        description="A 58-year-old male with known hypertension and type 2 diabetes presenting for routine follow-up.",
        expected_chief_complaint="Blood pressure management and medication review",
        transcript="""Doctor: Good morning, Mr. Johnson. How have you been since your last visit?

Patient: Morning, doctor. I've been doing okay, but my home blood pressure readings have been a bit high lately. I've been getting readings around 155 over 95 most mornings.

Doctor: I see. Are you taking your medications regularly?

Patient: Yes, I've been taking the lisinopril 10mg every morning with breakfast. And the metformin for my diabetes twice a day.

Doctor: Good. Any side effects from the medications? Dizziness, cough, anything like that?

Patient: I do have a little dry cough, but it's been there for a while. Nothing too bothersome.

Doctor: Any chest pain, shortness of breath, or headaches?

Patient: Occasional headaches, especially in the morning. No chest pain. Maybe a little short of breath when I climb stairs, but I've been less active lately.

Doctor: Let me check your vitals. Your blood pressure today is 158 over 92. Heart rate is 78 and regular. Temperature 98.6. Your weight is 210 pounds, up 4 pounds from last visit. Let me take a look at you.

Patient: I've been eating out more because of work stress.

Doctor: Heart sounds are regular, no murmurs. Lungs are clear to auscultation bilaterally. No peripheral edema. Your last labs from 3 months ago showed fasting glucose at 142 and HbA1c at 7.8%.

Patient: Is that good?

Doctor: The A1c is a bit above our target of 7%. We should also check your kidney function given the lisinopril. I'd like to increase your lisinopril to 20mg daily to better control your blood pressure. For your diabetes, let's also increase metformin to 1000mg twice daily if you're tolerating the current dose well. I want you to come back in 6 weeks for repeat labs — BMP and HbA1c. In the meantime, try to reduce sodium intake and aim for 30 minutes of walking most days. Also monitor your blood pressure at home and keep a log.

Patient: Okay, I can do that. Should I be worried about my kidneys?

Doctor: The ACE inhibitor actually protects the kidneys in diabetic patients, so it's a good medication for you. We just monitor the levels to make sure everything stays in range. Any other concerns today?

Patient: No, I think that covers everything.

Doctor: Great. Schedule follow-up in 6 weeks. Call us sooner if your BP goes above 180 over 110 or if you have any chest pain or severe headache.""",
    ),
    DemoTranscriptResponse(
        title="Acute Respiratory Complaint",
        description="A 34-year-old female presenting with 5 days of productive cough, fever, and shortness of breath.",
        expected_chief_complaint="Productive cough with fever and dyspnea",
        transcript="""Doctor: Hi Sarah, what brings you in today?

Patient: Hi doctor. I've had this terrible cough for about 5 days now and I started running a fever yesterday. I'm also having some trouble breathing when I do anything physical.

Doctor: Tell me more about the cough. Is it dry or are you bringing anything up?

Patient: It's productive. The mucus was clear at first but it's turned yellowish-green over the last two days.

Doctor: Any chest pain when you breathe?

Patient: Yes, a sharp pain on the right side when I take a deep breath or cough.

Doctor: How high has the fever been?

Patient: I measured it at home — it was 101.8 this morning. Last night it hit 102.4.

Doctor: Any chills, night sweats, or body aches?

Patient: Definitely chills. And I've been very fatigued. My whole body aches.

Doctor: Any sick contacts? Anyone around you been ill?

Patient: My coworker was out sick last week with something similar.

Doctor: Any history of asthma, COPD, or previous pneumonias?

Patient: No, I've always been pretty healthy. No major medical history. I'm not on any regular medications. I have a penicillin allergy — I got a rash from it as a child.

Doctor: Okay, important to note. Let me examine you. Your temperature is 101.2, blood pressure 118 over 74, heart rate 98, respiratory rate 20, oxygen saturation 94% on room air.

Patient: Is 94 okay?

Doctor: It's a little lower than I'd like to see. On exam, I hear decreased breath sounds and dullness to percussion over the right lower lobe. There's also some egophony present. Cardiovascular exam is normal, no murmurs.

Patient: What does that mean?

Doctor: Based on your symptoms and exam findings — fever, productive cough with purulent sputum, pleuritic chest pain, decreased breath sounds in the right lower lobe, and the low oxygen saturation — I'm concerned you have community-acquired pneumonia affecting your right lower lobe. I'd like to get a chest X-ray to confirm and check some labs including a CBC and CMP.

Patient: Do I need to be admitted to the hospital?

Doctor: Given your oxygen saturation, I want to see the chest X-ray first. If your O2 improves with the treatment and you can tolerate oral medications, we can likely manage you outpatient. Since you're allergic to penicillin, I'll prescribe azithromycin 500mg today, then 250mg daily for 4 days, along with doxycycline 100mg twice daily for 5 days for better coverage. I want you to take acetaminophen or ibuprofen for the fever and stay well hydrated. If your oxygen drops below 92%, you develop worsening shortness of breath at rest, or your fever goes above 103.5, go to the emergency room immediately. Otherwise, follow up with me in 48 hours.

Patient: Okay, I understand. Thank you doctor.""",
    ),
    DemoTranscriptResponse(
        title="Pediatric Well Visit",
        description="A 6-year-old boy presenting for annual well-child check with his mother.",
        expected_chief_complaint="Annual well-child examination, age 6",
        transcript="""Doctor: Hi there! You must be Tyler. And you're mom, Mrs. Chen?

Mother: Yes, that's right. He's here for his annual checkup.

Doctor: Great. Tyler, how are you doing today?

Tyler: Good.

Doctor: Are you eating okay? Any problems with eating?

Mother: He eats pretty well. He's been a good eater. Maybe a little picky about vegetables.

Doctor: That's pretty normal for his age. How is he doing in school?

Mother: He just started first grade. He loves it. His teacher says he's doing well. He's reading at grade level.

Doctor: Wonderful. Any behavioral concerns? Sleep issues?

Mother: He sleeps well, about 9 to 10 hours. He can be a handful sometimes but nothing I'd call a behavioral problem. He's a very active kid.

Doctor: Is he getting regular physical activity?

Mother: Yes, he plays soccer on weekends and rides his bike.

Doctor: Perfect. Any chronic medical conditions, allergies, or medications?

Mother: No medications. No known allergies. He had a febrile seizure when he was 18 months but nothing since then. His immunizations are up to date.

Doctor: Great. Let me do the examination. Tyler, can you hop up on the table for me? His weight is 46 pounds — that's the 55th percentile. Height is 45.5 inches — 50th percentile. BMI is 15.2, also in the healthy range. Blood pressure is 96 over 58. Vision screening shows 20/20 bilaterally. Hearing screen passed.

On physical exam: he's alert and cooperative. HEENT — ears clear, tympanic membranes intact, oropharynx clear, no lymphadenopathy. Cardiovascular — regular rate and rhythm, no murmurs. Lungs clear to auscultation. Abdomen soft, no organomegaly. Musculoskeletal — normal gait, full range of motion. Neurological exam appropriate for age.

Doctor: Tyler, do you wear a bike helmet when you ride?

Tyler: Sometimes.

Mother: We're working on that.

Doctor: It's really important every single time. Falls are the most common cause of head injury in kids his age. Tyler is meeting all developmental milestones appropriately. Growth parameters are normal. I'm recommending he receive the DTaP booster and influenza vaccine today since he's due. I'd also recommend limiting screen time to 1 to 2 hours per day of quality content, ensuring continued physical activity, and maintaining a balanced diet with plenty of fruits and vegetables. Please schedule the next well visit in one year at age 7. Any questions?

Mother: Should we be worried about his teeth? He lost his first tooth last month.

Doctor: That's completely normal. Make sure he's brushing twice a day with a fluoride toothpaste and flossing. He should be seeing a dentist every 6 months. Everything looks great today.""",
    ),
    DemoTranscriptResponse(
        title="Mental Health Consultation",
        description="A 29-year-old female presenting with 6-week history of low mood, anhedonia, and fatigue.",
        expected_chief_complaint="Depression screening, low mood and anhedonia",
        transcript="""Doctor: Good afternoon. What brings you in today?

Patient: Hi. I've been feeling really down for the past month and a half. I just don't feel like myself.

Doctor: Can you tell me more about what you mean by feeling down?

Patient: I used to love going out with friends, cooking, going to the gym. Now none of it feels enjoyable. I just want to stay in bed. I'm tired all the time even though I'm sleeping too much — like 10, 11 hours a day.

Doctor: How has your appetite been?

Patient: I've been eating less. I've probably lost 5 or 6 pounds without trying. Nothing sounds good to eat.

Doctor: Are you having trouble concentrating or making decisions?

Patient: Yes. At work, I keep making little mistakes. My boss asked if everything was okay. I can't focus on anything for more than a few minutes.

Doctor: Have you had any thoughts of hurting yourself or not wanting to be alive?

Patient: I haven't thought about hurting myself. But I have had thoughts like... what's the point, or wishing I could just disappear for a while. Not doing anything, but those thoughts have been there.

Doctor: Thank you for being honest with me. That takes courage. How are things at home and work?

Patient: I broke up with my boyfriend two months ago. It was mutual but it's been hard. Work has been stressful. I feel like I'm falling behind everywhere.

Doctor: Any history of depression or anxiety before? Any mental health treatment in the past?

Patient: I had some anxiety in college. I saw a counselor but never took any medication.

Doctor: Any family history of depression or other mental health conditions?

Patient: My mom has depression. She takes medication for it.

Doctor: Are you using any alcohol or substances to cope?

Patient: I've been drinking more wine than usual. Maybe a glass or two every night, sometimes three on weekends.

Doctor: Okay. Let me do a brief assessment. Your PHQ-9 score today is 16, which indicates moderately severe depression. You are not in immediate danger based on our conversation. I want to discuss next steps. I'm recommending we start you on sertraline 50mg daily to begin with — we'll titrate up as needed. I'm also referring you to a therapist for cognitive behavioral therapy, which works well alongside medication. I want you to reduce the alcohol consumption as it's a depressant and will worsen your mood. Let's follow up in 4 weeks. If you have any thoughts of harming yourself before then, please call 988 — the Suicide and Crisis Lifeline — or go to the nearest emergency room.

Patient: Okay. Will the medication help quickly?

Doctor: It typically takes 2 to 4 weeks to notice improvement. Some people feel a little worse in the first week before they feel better. That's normal and expected. Any questions?

Patient: No, I think I understand. Thank you for taking me seriously.

Doctor: Of course. You did the right thing by coming in.""",
    ),
    DemoTranscriptResponse(
        title="Emergency Chest Pain",
        description="A 52-year-old male presenting to the emergency department with acute onset chest pain and diaphoresis.",
        expected_chief_complaint="Acute chest pain with diaphoresis, rule out ACS",
        transcript="""Nurse: Mr. Davis, I'm the nurse. Can you tell me what's going on?

Patient: I have really bad chest pain. It started about 45 minutes ago. I was just sitting watching TV and it came on suddenly.

Doctor: Mr. Davis, I'm Dr. Patel. Can you describe the pain for me?

Patient: It's like a crushing pressure right here in the middle of my chest. It's about an 8 out of 10. And I feel like I'm sweating even though I'm not hot.

Doctor: Is the pain going anywhere — your arm, jaw, or back?

Patient: It's going down my left arm. And I feel a little nauseated.

Doctor: How long have you had this?

Patient: About 45 minutes now. It hasn't gotten better.

Doctor: Any history of heart problems? High blood pressure? Diabetes?

Patient: I have high blood pressure. I take lisinopril for it. My father had a heart attack at 56.

Doctor: Do you smoke?

Patient: I quit 5 years ago. Smoked for 20 years before that.

Doctor: Okay. We're moving quickly. We have your vitals: BP is 162 over 98, heart rate 110 and regular, respiratory rate 22, O2 sat 96% on room air. You're diaphoretic. EKG shows ST elevations in leads II, III, and aVF with reciprocal changes in the anterior leads. That's consistent with an inferior STEMI.

Patient: What does that mean? Am I having a heart attack?

Doctor: Yes, you are having a heart attack affecting the inferior wall of your heart. We need to act fast. We're activating the cardiac catheterization lab right now for emergency angioplasty. I'm starting you on aspirin 325mg chewed, nitroglycerin sublingual, a heparin drip, and oxygen. I'm also giving you a loading dose of ticagrelor. We'll have you in the cath lab within 30 minutes. Do you have any allergies?

Patient: No allergies. Is this going to kill me?

Doctor: You got here quickly and we're moving fast. That significantly improves your outcome. We're doing everything right. I need you to stay as calm as possible. We're going to take good care of you. Is there someone we should call?

Patient: My wife, Linda. Her number is in my phone.

Doctor: We'll call her right away. The cath lab team is ready.""",
    ),
    DemoTranscriptResponse(
        title="Chronic Pain Management",
        description="A 44-year-old female with fibromyalgia presenting for ongoing pain management and medication review.",
        expected_chief_complaint="Fibromyalgia — widespread pain, fatigue, sleep dysfunction",
        transcript="""Doctor: Good morning, Mrs. Torres. How have things been since last month?

Patient: Honestly, not great, doctor. The pain has been more widespread. My shoulders, hips, and lower back are the worst. My sleep is terrible — I wake up every few hours and never feel rested.

Doctor: On a scale of 1 to 10, what's your average pain level this past week?

Patient: Most days about a 6. Some days it spikes to 8 or 9, especially after any physical activity.

Doctor: Are you still doing the aquatic therapy?

Patient: I went twice last week. It helped a little during the session but I was exhausted for two days after.

Doctor: That post-exertional fatigue is very common with fibromyalgia. It's called post-exertional malaise. Pushing too hard can set you back. How about your mood? Any depression or anxiety?

Patient: The pain wears me down emotionally. Some days I feel hopeless. I'm still on the duloxetine though.

Doctor: Good. Are you noticing any benefit from the duloxetine at 60mg?

Patient: Maybe a little. The edge has been taken off compared to before I started it.

Doctor: Let me examine you. Vital signs: BP 118 over 76, HR 72, temp 98.4. On exam, you have diffuse tenderness to palpation at classic fibromyalgia tender points — bilateral trapezius, suboccipital, lateral epicondyle, and greater trochanteric areas. No joint swelling or erythema. Neurological exam is intact.

Doctor: Your TSH from last month was normal and your CBC and CMP were unremarkable, which rules out other causes.

Patient: Is there anything we can add or change? The duloxetine alone doesn't feel like enough.

Doctor: I'd like to add low-dose cyclobenzaprine 5mg at bedtime to help with your sleep and muscle tension. I also want to refer you to a pain psychologist for CBT, which has good evidence for fibromyalgia. Continue the aquatic therapy but limit sessions to 20 to 30 minutes. I also want to discuss sleep hygiene — avoiding screens an hour before bed, consistent wake times even on weekends. We'll check back in 6 weeks.

Patient: Okay. I appreciate you listening. A lot of doctors dismiss fibromyalgia.

Doctor: It's a real condition and it significantly affects quality of life. We're going to keep working on this together.""",
    ),
    DemoTranscriptResponse(
        title="Orthopedic Knee Evaluation",
        description="A 38-year-old recreational runner presenting with 3-week history of right knee pain after a trail run.",
        expected_chief_complaint="Right knee pain, possible lateral meniscus injury",
        transcript="""Doctor: Hi there. So you're having some knee trouble?

Patient: Yes, my right knee. I was doing a trail run about three weeks ago and felt a pop on the outside of my knee when I came downhill. It swelled up pretty fast.

Doctor: Did you fall or twist it?

Patient: I didn't fall. It felt like I just landed awkwardly on a downhill section. Immediate pain on the outer side of the knee.

Doctor: How is it now compared to right after?

Patient: The swelling went down a lot. But it still hurts when I go down stairs or when I try to run. Sometimes it feels like something is catching inside.

Doctor: Any giving way? Does your knee buckle or feel unstable?

Patient: Not really buckling, but it does feel like it catches sometimes when I bend it.

Doctor: Any numbness, tingling, or weakness in your leg?

Patient: No, nothing like that.

Doctor: What's your activity level normally? Any prior knee injuries?

Patient: I run about 30 miles a week. I sprained my ankle on the same side a couple years ago but no knee problems before this.

Doctor: Let me examine you. Vital signs are normal. On inspection, mild effusion of the right knee, no erythema. ROM — full flexion and extension with pain at 110 degrees flexion. Palpation — point tenderness over the lateral joint line. McMurray test positive for lateral compartment with an audible click. Valgus stress test — no instability. Lachman and anterior drawer tests — negative, ACL appears intact. Pivot shift — negative.

Patient: What do you think is going on?

Doctor: Based on the mechanism — an audible pop with immediate lateral knee swelling during a downhill run, positive McMurray test, lateral joint line tenderness — I'm highly suspicious for a lateral meniscus tear. I'd like to get an MRI of the right knee without contrast to characterize the tear.

Patient: Will I need surgery?

Doctor: It depends on the type and location of the tear. Many meniscus tears can be treated conservatively with physical therapy. If it's a bucket-handle tear or if conservative treatment fails, arthroscopy may be needed. For now, I want you to stop running and avoid deep squatting. Ice and NSAIDs — ibuprofen 600mg three times daily with food for one week. Start PT for quad strengthening and range of motion. We'll review the MRI findings at your next appointment. Any questions?

Patient: How long until I can run again?

Doctor: That depends on the MRI and your response to PT. With conservative management, some patients return to running in 6 to 12 weeks. We'll have a clearer picture once we see the imaging.""",
    ),
    DemoTranscriptResponse(
        title="New-Onset Type 2 Diabetes",
        description="A 47-year-old obese male with newly diagnosed type 2 diabetes referred for initial management.",
        expected_chief_complaint="New diagnosis of type 2 diabetes mellitus for initial management and education",
        transcript="""Doctor: Mr. Okafor, I'm glad you came in. Your primary care doctor sent your labs over. Let's talk about what they showed and what it means.

Patient: I'm a little scared, honestly. He said my blood sugar was very high.

Doctor: Your fasting glucose was 238 and your HbA1c came back at 9.4%. That confirms a diagnosis of type 2 diabetes. Let's talk about what that means and how we're going to manage it.

Patient: I suspected something was off. I've been really thirsty all the time and urinating frequently, especially at night.

Doctor: Yes, those are classic symptoms of high blood sugar — it spills into the urine and pulls water with it. Any blurry vision?

Patient: A little, yes. I thought I needed new glasses.

Doctor: That can be from the diabetes as well. When blood sugar is high, the lens of the eye swells. Once we get your glucose under control, vision often improves. Have you had any numbness or tingling in your feet?

Patient: Actually yes, my feet tingle at night sometimes.

Doctor: That could be early diabetic neuropathy. Let me do a quick exam. Your weight is 247 pounds, height 5 foot 10, BMI is 35.4 — that's in the obese range. BP is 138 over 84. Monofilament foot exam shows mildly reduced sensation bilateral feet. Fundoscopic exam — limited here but I'll refer you for a dilated eye exam.

Doctor: Here's what we're going to do. I'm starting you on metformin 500mg twice daily with meals — we'll increase to 1000mg in two weeks if you tolerate it. I'm also referring you to our diabetes education program, a registered dietitian, and a certified diabetes educator. I want you to check your fasting blood glucose every morning and log it. Let's check an HbA1c in 3 months. I'm also ordering a urine microalbumin to check kidney function, a lipid panel, and an EKG.

Patient: Do I have to be on medication forever?

Doctor: Not necessarily. Type 2 diabetes is strongly influenced by lifestyle. Weight loss of even 5 to 10 percent of your body weight, dietary changes, and regular exercise can significantly improve your blood sugar — sometimes enough to reduce or stop medications. This is a serious condition but it's very manageable if we work together.

Patient: What should I eat?

Doctor: That's exactly what the dietitian will help you with. In general, reduce refined carbohydrates and sugars, increase vegetables and lean proteins, watch your portions. Aim for 30 minutes of walking 5 days a week. Small, sustainable changes are better than a perfect diet you can't maintain.

Patient: Okay. I want to get this under control.

Doctor: That attitude is everything. Let's schedule your follow-up in 4 weeks.""",
    ),
]


@router.get("/demo-transcript", response_model=DemoTranscriptResponse, tags=["Demo"])
async def get_demo_transcript(
    index: int = Query(default=0, ge=0, le=7, description="Demo transcript index (0-7)")
) -> DemoTranscriptResponse:
    """Returns a pre-loaded demo transcript for testing the generation pipeline."""
    return DEMO_TRANSCRIPTS[index]


@router.get("/demo-transcripts/list", tags=["Demo"])
async def list_demo_transcripts() -> list[dict]:
    """Returns metadata for all available demo transcripts."""
    return [
        {"index": i, "title": t.title, "description": t.description}
        for i, t in enumerate(DEMO_TRANSCRIPTS)
    ]
