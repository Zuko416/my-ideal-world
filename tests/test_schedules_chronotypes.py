"""Tests for chronotypes, age-based schedule variations, and occupation decoupling."""
import unittest
from npc_sim.core.npc import NPC
from npc_sim.core.schedule import (
    ActivityType,
    Chronotype,
    ScheduleBlock,
    DailySchedule,
    create_daily_schedule,
)


class TestSchedulesChronotypes(unittest.TestCase):
    def test_schedule_block_covers_day_and_wrap(self):
        day_block = ScheduleBlock(8, 17, ActivityType.WORK)
        self.assertTrue(day_block.covers(8))
        self.assertTrue(day_block.covers(12))
        self.assertFalse(day_block.covers(17))
        self.assertFalse(day_block.covers(7))

        night_block = ScheduleBlock(23, 7, ActivityType.SLEEP)
        self.assertTrue(night_block.covers(23))
        self.assertTrue(night_block.covers(2))
        self.assertTrue(night_block.covers(6))
        self.assertFalse(night_block.covers(7))
        self.assertFalse(night_block.covers(15))

    def test_chronotype_sleep_wake_timing(self):
        # Early riser (sleep 21:00 - 05:00)
        early_sched = create_daily_schedule(age=30, chronotype=Chronotype.EARLY_RISER)
        self.assertEqual(early_sched.get_desired_activity(22).activity, ActivityType.SLEEP)
        self.assertEqual(early_sched.get_desired_activity(4).activity, ActivityType.SLEEP)
        self.assertNotEqual(early_sched.get_desired_activity(6).activity, ActivityType.SLEEP)

        # Nocturnal (sleep 09:00 - 17:00)
        nocturnal_sched = create_daily_schedule(age=30, chronotype=Chronotype.NOCTURNAL)
        self.assertEqual(nocturnal_sched.get_desired_activity(10).activity, ActivityType.SLEEP)
        self.assertEqual(nocturnal_sched.get_desired_activity(14).activity, ActivityType.SLEEP)
        self.assertEqual(nocturnal_sched.get_desired_activity(23).activity, ActivityType.SOCIALIZE)

    def test_chronotype_decoupled_from_occupation(self):
        # A nocturnal NPC who is a farmer: occupation sets work shift, chronotype sets sleep preference
        farmer_sched = create_daily_schedule(
            age=35,
            chronotype=Chronotype.NOCTURNAL,
            occupation="farmer",
            work_location="fields",
        )
        work_block = farmer_sched.get_desired_activity(10)
        # Farmer occupation mandates work at 10:00 despite nocturnal preference
        self.assertEqual(work_block.activity, ActivityType.WORK)
        self.assertEqual(work_block.target_location, "fields")

    def test_age_schedule_differences(self):
        toddler_sched = create_daily_schedule(age=2)
        child_sched = create_daily_schedule(age=9)
        adult_sched = create_daily_schedule(age=35, occupation="worker")

        # Toddler has nap/rest at 13:00
        self.assertEqual(toddler_sched.get_desired_activity(13).activity, ActivityType.REST)
        # 9-year old has school at 10:00
        self.assertEqual(child_sched.get_desired_activity(10).activity, ActivityType.SCHOOL)
        # Adult worker has work at 10:00
        self.assertEqual(adult_sched.get_desired_activity(10).activity, ActivityType.WORK)

    def test_individual_routine_diversity_same_age(self):
        # Two 25-year-olds with different occupations and chronotypes
        npc_a = NPC("Alice", age=25, chronotype=Chronotype.EARLY_RISER, occupation="doctor")
        npc_b = NPC("Bob", age=25, chronotype=Chronotype.LATE_SLEEPER, occupation="resident")

        # At 05:30 (hour 5), Alice is awake eating breakfast; Bob is asleep
        self.assertEqual(npc_a.get_scheduled_activity(5).activity, ActivityType.MEAL)
        self.assertEqual(npc_b.get_scheduled_activity(5).activity, ActivityType.SLEEP)


if __name__ == "__main__":
    unittest.main()
