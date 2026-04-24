How the Grading System Works — End to End

**Phase 1 — Build the Blueprint (one time per exam)**

1. Upload the exam paper Teacher uploads the question paper PDF for their class:

POST /agents/grading/exam-papers
  class_id=5, file=exam1.pdf
→ { exam_paper_id: 1 }

This is stored permanently. The same exam can be uploaded to multiple classes — the file won't be duplicated on disk (sha256 dedup).
2. Analyse and create the blueprint Teacher opens the analyse form and fills in:
Selects the exam paper they just uploaded (exam_paper_id: 1)
Optionally selects lesson docs from their class (already embedded in Weaviate)
Optionally uploads a correction PDF (their model answer)
Types grading preferences: "Q1 = 4pts, deduct 1pt for missing units"
Types style guide: "Math: show all steps, use exact values"
Gives a title: "Exam 1 Correction – 2026"
Hits Analyse
POST /agents/grading/analyse  →  SSE stream opens 

The agent runs:

Calls read_pdf_as_images(exam_file_path) → reads all exam pages as images → sends to VLM
If correction PDF provided: calls read_pdf_as_images(correction_file_path) → reads model answers
If it needs lesson context (e.g. to understand how a topic is graded): calls rag_retrieve(query, doc_ids) → searches Weaviate
Applies teacher preferences + style guide
Writes its understanding as a blueprint summary (one line per question: label, max points, criteria)

Meanwhile the frontend streams:

thinking tokens → show in collapsible reasoning panel
content tokens → show in main area
tool_call / tool_result → show "Reading exam..." / "Searching lessons..." indicators
blueprint_ready → graph suspends — this suspended checkpoint in Postgres IS the blueprint
blueprint_saved → DB row written → frontend stores blueprint_id: 42
Correction PDF is deleted from disk at this point (one-time artifact)
The blueprint is now reusable for any class. The agent's full understanding (all those images + reasoning) is frozen in the Postgres checkpoint.

**Phase 2 — Grade a Batch of Students**

3. Submit student exam PDFs Teacher goes into class mode, selects:
The blueprint they created (blueprint_id: 42)
The class (class_id: 5) and exam type (exam_type_id: 3)
Assigns each enrolled student their exam PDF

POST /agents/grading/grade  (multipart)
  blueprint_id=42, class_id=5, exam_type_id=3
  student_ids[]=10, exam_pdfs[]=alice.pdf
  student_ids[]=11, exam_pdfs[]=bob.pdf
  student_ids[]=12, exam_pdfs[]=charlie.pdf

→ {
    first_session_id: "uuid-s1",
    sessions: [
      { session_id: "uuid-s1", student_name: "Alice D.", queue_position: 0 },
      { session_id: "uuid-s2", student_name: "Bob M.",   queue_position: 1 },
      { session_id: "uuid-s3", student_name: "Charlie R.", queue_position: 2 }
    ]
  }

Backend: validates enrollment for each student, sorts them alphabetically by display_name (what the teacher sees in their class), saves each PDF permanently, creates GradingSession rows. No LLM involved yet.

4. Grade student #1 (Alice) Frontend opens SSE stream for first_session_id:

GET /agents/grading/sessions/uuid-s1/stream

Backend forks the blueprint checkpoint → Alice's thread (SQL copy of all Postgres checkpoint tables). The agent now starts from the exact point where it finished understanding the exam — full exam context already in its window.
The agent calls read_pdf_as_images(alice_exam_path) → reads Alice's answers → grades each question:

event: question_result
data: {"question_number":1,"label":"Q1","max_points":4,"awarded_points":3,
       "reasoning":"Correctly defined KNN but missed the distance metric (-1pt)."}

event: question_result
data: {"question_number":2,"label":"Q2","max_points":6,"awarded_points":6,
       "reasoning":"Full derivation with correct formula. All steps shown."}
...

event: interrupt
data: {"breakdown": [...all questions...]}

Graph suspends — waits for teacher decision.
5. Teacher reviews Alice's grade Frontend shows a per-question breakdown card. 
Teacher sees the agent's reasoning for every point deducted. They can edit any score. When satisfied:

POST /agents/grading/sessions/uuid-s1/review
  { action: "approve", decisions: [{question_number:1, awarded_points:2.5}, {question_number:2, awarded_points:6}] }

→ {
    action: "approved",
    total_awarded: 8.5,
    total_max: 10.0,
    normalised_grade: 17.0,   ← saved to grades table
    grade: { id: 55, value: 17.0 },
    next_session_id: "uuid-s2"   ← Bob is next
  }

Grade is saved in the grades table. Alice's session checkpoint is kept in Postgres but no longer needed.

6. Repeat for Bob, then Charlie Frontend immediately opens GET /sessions/uuid-s2/stream. Bob's session forks 
fresh from the blueprint (not from Alice's session — completely isolated context window). Same flow. When Bob is approved/cancelled,
next_session_id: "uuid-s3". After Charlie: next_session_id: null → batch complete.

Teacher Disconnects Mid-Batch
Teacher grades Alice, approves, then closes the tab.
On return:

GET /agents/grading/sessions?batch_id=uuid-batch
→ sessions: [ {status:"approved"}, {status:"pending"}, {status:"pending"} ]

Frontend finds the first pending (Bob) ordered by queue_position and resumes exactly there. Bob's PDF is already saved on disk, blueprint is still in Postgres — 
nothing is lost.