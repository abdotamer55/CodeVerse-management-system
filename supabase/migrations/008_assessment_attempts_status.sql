-- ==============================================================================
-- CodeVerse LMS: Expand assessment_attempts status check constraint
-- Migration: 008_assessment_attempts_status.sql
-- ==============================================================================

ALTER TABLE assessment_attempts DROP CONSTRAINT IF EXISTS assessment_attempts_status_check;
ALTER TABLE assessment_attempts ADD CONSTRAINT assessment_attempts_status_check 
    CHECK (status IN ('in_progress', 'submitted', 'expired', 'pending_essay_grading', 'graded'));
