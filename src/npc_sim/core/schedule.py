"""Daily schedules, activity blocks, chronotypes, and routine composition."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from npc_sim.core.traits import AgeGroup, get_age_group


class ActivityType(Enum):
    SLEEP = "sleep"
    WAKE = "wake"
    MEAL = "meal"
    WORK = "work"
    SCHOOL = "school"
    SOCIALIZE = "socialize"
    RECREATION = "recreation"
    ERRAND = "errand"
    REST = "rest"
    IDLE = "idle"


class Chronotype(Enum):
    EARLY_RISER = "early_riser"  # Prefers sleep 21:00 - 05:00
    NORMAL = "normal"            # Prefers sleep 23:00 - 07:00
    LATE_SLEEPER = "late_sleeper"# Prefers sleep 01:00 - 09:00
    NOCTURNAL = "nocturnal"      # Prefers sleep 09:00 - 17:00


@dataclass
class ScheduleBlock:
    """A scheduled activity period within a 24-hour cycle."""
    start_hour: int
    end_hour: int
    activity: ActivityType
    target_location: Optional[str] = None
    base_weight: float = 0.5

    def covers(self, hour: int) -> bool:
        """Check if this block covers the specified hour (0-23), supporting midnight wrap."""
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        else:
            # Wraps past midnight (e.g. 23 to 7)
            return hour >= self.start_hour or hour < self.end_hour


@dataclass
class DailySchedule:
    """An NPC's 24-hour schedule comprised of activity blocks."""
    blocks: List[ScheduleBlock] = field(default_factory=list)

    def get_desired_activity(self, hour: int) -> ScheduleBlock:
        """Find the scheduled activity block for a specific hour."""
        for block in self.blocks:
            if block.covers(hour):
                return block
        return ScheduleBlock(
            start_hour=hour,
            end_hour=(hour + 1) % 24,
            activity=ActivityType.IDLE,
            base_weight=0.2,
        )


def create_daily_schedule(
    age: int,
    chronotype: Chronotype = Chronotype.NORMAL,
    occupation: str = "resident",
    home_location: str = "house",
    work_location: Optional[str] = None,
    social_location: str = "square",
) -> DailySchedule:
    """
    Construct an individual daily schedule based on:
    - chronotype (sleep/wake timing preference)
    - occupation requirements (work hours and location)
    - age group capabilities (school, naps, play)
    - personal locations (home, work, social spots)
    """
    age_group = get_age_group(age)
    blocks: List[ScheduleBlock] = []

    # 1. Determine Sleep Window based on chronotype & age
    if age_group == AgeGroup.TODDLER:
        sleep_start, sleep_end = 19, 6
    elif age_group == AgeGroup.YOUNG_CHILD:
        sleep_start, sleep_end = 20, 7
    elif chronotype == Chronotype.EARLY_RISER:
        sleep_start, sleep_end = 21, 5
    elif chronotype == Chronotype.LATE_SLEEPER:
        sleep_start, sleep_end = 1, 9
    elif chronotype == Chronotype.NOCTURNAL:
        sleep_start, sleep_end = 9, 17
    else:  # NORMAL
        sleep_start, sleep_end = 23, 7

    # 2. Add Age / Occupation Obligations
    if age_group == AgeGroup.TODDLER:
        blocks.append(ScheduleBlock(sleep_start, sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))
        blocks.append(ScheduleBlock(6, 8, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
        blocks.append(ScheduleBlock(8, 12, ActivityType.RECREATION, target_location=home_location, base_weight=0.4))
        blocks.append(ScheduleBlock(12, 14, ActivityType.REST, target_location=home_location, base_weight=0.6))
        blocks.append(ScheduleBlock(14, 18, ActivityType.RECREATION, target_location=home_location, base_weight=0.4))
        blocks.append(ScheduleBlock(18, 19, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

    elif age_group in (AgeGroup.YOUNG_CHILD, AgeGroup.OLDER_CHILD):
        blocks.append(ScheduleBlock(sleep_start, sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))
        school_loc = work_location or "school"
        wake_hour = sleep_end
        blocks.append(ScheduleBlock(wake_hour, (wake_hour + 1) % 24, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
        blocks.append(ScheduleBlock(8, 14, ActivityType.SCHOOL, target_location=school_loc, base_weight=0.6))
        blocks.append(ScheduleBlock(14, 17, ActivityType.RECREATION, target_location=social_location, base_weight=0.5))
        blocks.append(ScheduleBlock(17, 19, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
        blocks.append(ScheduleBlock(19, sleep_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

    elif occupation in ("worker", "doctor", "farmer", "shopkeeper", "tradesperson", "teacher"):
        work_loc = work_location or home_location
        if occupation == "farmer":
            work_start, work_end = 6, 15
        elif occupation == "doctor":
            work_start, work_end = 8, 17
        elif occupation == "shopkeeper":
            work_start, work_end = 9, 18
        else:
            work_start, work_end = 8, 16

        # Work obligation is prioritized in daytime
        blocks.append(ScheduleBlock(work_start, work_end, ActivityType.WORK, target_location=work_loc, base_weight=0.6))

        # Adjust sleep block around work if there is a conflict (e.g. nocturnal person with day job)
        if work_start <= sleep_start < work_end or work_start < sleep_end <= work_end:
            # Shift sleep to night or off-work hours
            adjusted_sleep_start = (work_end + 6) % 24
            adjusted_sleep_end = (work_start - 1) % 24
            blocks.append(ScheduleBlock(adjusted_sleep_start, adjusted_sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))
            blocks.append(ScheduleBlock((adjusted_sleep_end) % 24, work_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock(work_end, (work_end + 3) % 24, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock((work_end + 3) % 24, adjusted_sleep_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
        else:
            blocks.append(ScheduleBlock(sleep_start, sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))
            wake_hour = sleep_end
            if wake_hour < work_start:
                blocks.append(ScheduleBlock(wake_hour, work_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
            if work_end < sleep_start:
                blocks.append(ScheduleBlock(work_end, (work_end + 3) % 24, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
                blocks.append(ScheduleBlock((work_end + 3) % 24, sleep_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

    else:
        # Flexible resident/elder/homemaker: sleep conforms to chronotype
        blocks.append(ScheduleBlock(sleep_start, sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))
        wake_hour = sleep_end
        if chronotype == Chronotype.NOCTURNAL:
            blocks.append(ScheduleBlock(17, 19, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock(19, 21, ActivityType.ERRAND, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock(21, 2, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock(2, 4, ActivityType.RECREATION, target_location=home_location, base_weight=0.4))
            blocks.append(ScheduleBlock(4, 7, ActivityType.REST, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock(7, 9, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
        else:
            blocks.append(ScheduleBlock(wake_hour, (wake_hour + 2) % 24, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock((wake_hour + 2) % 24, 14, ActivityType.ERRAND, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock(14, 16, ActivityType.REST, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock(16, 19, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock(19, sleep_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

    return DailySchedule(blocks=blocks)
