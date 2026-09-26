-- Migration 013: Add starts_at and ends_at columns to exams table for real exam scheduling
ALTER TABLE exams ADD COLUMN IF NOT EXISTS starts_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE exams ADD COLUMN IF NOT EXISTS ends_at TIMESTAMP WITH TIME ZONE;
