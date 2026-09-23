-- 007_lesson_live_url.sql
-- Add live_url column to lessons table to support live streaming platforms (YouTube Live, Zoom, Google Meet, Microsoft Teams)

ALTER TABLE lessons ADD COLUMN IF NOT EXISTS live_url TEXT;

COMMENT ON COLUMN lessons.live_url IS 'Direct streaming or room join URL for live lessons (YouTube Live embed/watch, Zoom, Google Meet, Teams)';
