from . import common

from src import actions, entities, events, geometry, jobs

class WarriorTest(common.EntityTest):
    def test_walking(self) -> None:
        speed = 1.0
        duration = 1.0
        ignored_bearing = 0.0
        ignored_location = geometry.Point(0.0, 0.0)

        warrior = entities.Warrior(0, (0.0, 0.0))
        self.world.add_entity(warrior)
        id = warrior.get_id()
        finish_event = events.FinishedEvent(id)

        for i, event in enumerate([events.ResumeEvent(id), finish_event]):
            old_task, new_task = self.handle_event(warrior, event)
            self.assertIsNot(old_task, new_task)

            if i == 0:
                expected_final = []
            else:
                expected_final = [actions.LocalizeAction(id, ignored_location)]
            expected_initial = [actions.MovementAction(id, duration, ignored_bearing, speed)]
            expected_job = jobs.MovementJob(id, speed, ignored_bearing, duration, [finish_event])

            self.assert_actions(old_task.finish(self.world), expected_final)
            self.assert_actions(new_task.start(self.world), expected_initial)
            self.assert_job(new_task.get_job(), expected_job)

