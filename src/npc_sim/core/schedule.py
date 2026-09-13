"""Daily schedules, chronotypes, and activity routine definitions."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from npc_sim.core.traits import AgeGroup, get_age_group


class ActivityType(Enum):
    """Types of routine and dynamic activities an NPC can engage in."""
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
    """Preferred sleep/wake timing profiles."""
    EARLY_RISER = "early_riser"    # Sleeps 21:00 - 05:00
    NORMAL = "normal"              # Sleeps 23:00 - 07:00
    LATE_SLEEPER = "late_sleeper"  # Sleeps 01:00 - 09:00
    NOCTURNAL = "nocturnal"        # Sleeps 09:00 - 17:00


@dataclass
class ScheduleBlock:
    """A designated activity span within a 24-hour cycle."""
    start_hour: int
    end_hour: int
    activity: ActivityType
    target_location: Optional[str] = None
    base_weight: float = 0.5

    def covers(self, hour: int) -> bool:
        """Check if an hour falls within this block (handles midnight wraparound)."""
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        else:
            # Crosses midnight (e.g., 23:00 to 07:00)
            return hour >= self.start_hour or hour < self.end_hour


@dataclass
class DailySchedule:
    """An NPC's full 24-hour routine profile."""
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


WORK_OCCUPATIONS = {
    "worker", "doctor", "farmer", "shopkeeper", "tradesperson", "teacher",
    "builder", "tailor", "herbalist", "farmhand", "blacksmith", "baker", "gardener"
}


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
        school_loc = work_location or "school"
        wake_hour = sleep_end
        blocks.append(ScheduleBlock(8, 14, ActivityType.SCHOOL, target_location=school_loc, base_weight=0.6))
        blocks.append(ScheduleBlock(sleep_start, sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))
        if wake_hour < 8:
            blocks.append(ScheduleBlock(wake_hour, 8, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
        blocks.append(ScheduleBlock(14, 17, ActivityType.RECREATION, target_location=social_location, base_weight=0.5))
        blocks.append(ScheduleBlock(17, 19, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
        blocks.append(ScheduleBlock(19, sleep_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

    elif occupation in WORK_OCCUPATIONS:
        work_loc = work_location or home_location
        if occupation in ("farmer", "farmhand"):
            work_start, work_end = 6, 15
        elif occupation == "doctor":
            work_start, work_end = 8, 17
        elif occupation in ("shopkeeper", "baker", "tailor"):
            work_start, work_end = 8, 17
        else:
            work_start, work_end = 8, 16

        # Work obligation takes priority during work hours
        blocks.append(ScheduleBlock(work_start, work_end, ActivityType.WORK, target_location=work_loc, base_weight=0.6))

        # Sleep block always at home
        blocks.append(ScheduleBlock(sleep_start, sleep_end, ActivityType.SLEEP, target_location=home_location, base_weight=0.7))

        # Morning window: waking to work start (only if wake occurs before work starts)
        wake_hour = sleep_end
        if wake_hour < work_start:
            blocks.append(ScheduleBlock(wake_hour, work_start, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

        # Evening social block at social spot (e.g. town square)
        social_end = 20 if sleep_start >= 22 or sleep_start <= 2 else 19
        if work_end < social_end:
            blocks.append(ScheduleBlock(work_end, social_end, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))

        # Evening meal (1 hour dinner at home)
        meal_end = (social_end + 1) % 24
        blocks.append(ScheduleBlock(social_end, meal_end, ActivityType.MEAL, target_location=home_location, base_weight=0.5))

        # Evening wind-down / rest before sleep at home
        if meal_end != sleep_start:
            blocks.append(ScheduleBlock(meal_end, sleep_start, ActivityType.REST, target_location=home_location, base_weight=0.5))

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
            if wake_hour < (wake_hour + 2) % 24:
                blocks.append(ScheduleBlock(wake_hour, (wake_hour + 2) % 24, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock((wake_hour + 2) % 24, 14, ActivityType.ERRAND, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock(14, 16, ActivityType.REST, target_location=home_location, base_weight=0.5))
            blocks.append(ScheduleBlock(16, 19, ActivityType.SOCIALIZE, target_location=social_location, base_weight=0.4))
            blocks.append(ScheduleBlock(19, (19 + 1) % 24, ActivityType.MEAL, target_location=home_location, base_weight=0.5))
            if 20 != sleep_start:
                blocks.append(ScheduleBlock(20, sleep_start, ActivityType.REST, target_location=home_location, base_weight=0.5))

    return DailySchedule(blocks=blocks)
