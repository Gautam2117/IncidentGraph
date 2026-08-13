from app.worker import celery_app, run_evaluation_task, run_investigation_task


def test_worker_tasks_are_registered_and_bounded() -> None:
    assert run_investigation_task.name == "incidentgraph.run_investigation"
    assert run_evaluation_task.name == "incidentgraph.run_evaluation"
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.task_time_limit == 1_800
    assert celery_app.conf.accept_content == ["json"]
