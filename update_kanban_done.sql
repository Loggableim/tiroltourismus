-- Run this against both Kanban DBs to set t_cloudflare_buildpipe to 'done'
-- DB 1: C:/HermesPortable/home/spaces/tirol-tourismus/kanban/boards/tirol-cicd/kanban.db
-- DB 2: C:/HermesPortable/home/kanban/boards/tirol-cicd/kanban.db

UPDATE tasks SET status='done' WHERE task_id='t_cloudflare_buildpipe';
