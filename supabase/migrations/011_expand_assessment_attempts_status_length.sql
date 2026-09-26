-- ==============================================================================
-- CodeVerse LMS: Expand assessment_attempts status column length
-- Migration: 011_expand_assessment_attempts_status_length.sql
-- ==============================================================================

ALTER TABLE assessment_attempts ALTER COLUMN status TYPE VARCHAR(50);
