-- Migration 012: Expand results.status length and update status check constraint
ALTER TABLE results ALTER COLUMN status TYPE VARCHAR(50);

ALTER TABLE results DROP CONSTRAINT IF EXISTS results_status_check;
ALTER TABLE results ADD CONSTRAINT results_status_check 
  CHECK (status IN ('passed', 'repeat', 'failed', 'review', 'pending_essay_grading'));
