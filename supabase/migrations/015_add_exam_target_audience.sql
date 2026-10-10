-- Migration: 015_add_exam_target_audience.sql
-- Allow targeting exams to all students or specific students

ALTER TABLE exams ADD COLUMN IF NOT EXISTS target_audience VARCHAR(20) DEFAULT 'all';
ALTER TABLE exams ADD COLUMN IF NOT EXISTS target_students JSONB DEFAULT '[]'::jsonb;
