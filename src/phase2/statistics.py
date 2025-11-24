import asyncio
from datetime import date, timedelta

from sqlalchemy import Boolean, Date, Integer, String, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

from phase2.leaderboard import Leaderboard

Base = declarative_base()


class RoundStatistics(Base):
    __tablename__ = "round_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True) # entry id
    user_id: Mapped[int] = mapped_column(Integer, nullable=False) # user id to users table
    # seconds it took to finish the round, storing as int then converting to timedelta
    time_to_complete_in_seconds: Mapped[int] = mapped_column(Integer, nullable=False)  
    won: Mapped[bool] = mapped_column(Boolean, nullable=False) # won or lost
    guesses: Mapped[int] = mapped_column(Integer, nullable=False) # number of guesses the round took
    mode: Mapped[str] = mapped_column(String(10), nullable=False) # gamemode, daily/survival
    daily_date: Mapped[date] = mapped_column(Date, nullable=False)  # the day this daily took place
    survival_streak: Mapped[int] = mapped_column(Integer, nullable=False)
    
# non ORM LeaderboardStats class
class LeaderboardStats:
    def __init__(self, 
                 user_id: int, 
                 daily_streak: int, 
                 longest_daily_streak: int, 
                 average_daily_guesses: int, 
                 average_daily_time: float, 
                 longest_survival_streak: int, 
                 score: int):
        
        self.user_id = user_id
        self.daily_streak = daily_streak
        self.longest_daily_streak = longest_daily_streak
        self.average_daily_guesses = average_daily_guesses
        self.average_daily_time = average_daily_time
        self.longest_survival_streak = longest_survival_streak
        self.score = score

class RoundStatisticsRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def add_round(self, *, 
                  user_id: int, 
                  time_to_complete_in_seconds: timedelta, 
                  won: bool, 
                  guesses: int, 
                  mode: str, 
                  daily_date: date, 
                  survival_streak: int) -> RoundStatistics:
        """
        Receives statistics for a round from the game, 
        updates the user's stats table accordingly and
        returns the RoundStatistics instance
        """
        round_row = RoundStatistics(
            user_id=user_id, 
            time_to_complete_in_seconds=int(time_to_complete_in_seconds.total_seconds()), 
            won=won,
            guesses=guesses, 
            mode=mode, 
            daily_date=daily_date, 
            survival_streak=survival_streak)
        
        self.session.add(round_row) # log the round stats
        
        lb_repo = Leaderboard(self.session)
        lb_repo.stats_repo = self
        asyncio.run(lb_repo.sync_user_entry(user_id))
        
        self.session.commit()
        return round_row

    def get_daily_round(self, user_id: int, day: date) -> RoundStatistics:
        """
        Get a daily round's stats by user_id and the date
        """
        statement = select(RoundStatistics).where(RoundStatistics.user_id == user_id, 
        RoundStatistics.mode == "daily", RoundStatistics.daily_date == day)
        return self.session.execute(statement).scalars().one_or_none()
    
    def get_leaderboard_stats_for_user(self, user_id: int) -> LeaderboardStats or None:
        """
        Grab and put RoundStatistics rows for this user into a single
        LeaderboardStats object (same shape as FakeStats in tests).
        """
        statement = select(RoundStatistics).where(RoundStatistics.user_id == user_id)
        rounds = self.session.execute(statement).scalars().all()

        if not rounds:
            return None

        daily_rounds = [r for r in rounds if r.mode == "daily"]
        survival_rounds = [r for r in rounds if r.mode == "survival"]

        daily_streak = 0
        longest_daily_streak = 0

        if daily_rounds:
            # get rounds sorted by date to check streaks 
            daily_rounds_sorted = sorted(daily_rounds, key=lambda r: r.daily_date) 

            current = 0
            for r in daily_rounds_sorted:
                if r.won:
                    current += 1
                    if current > longest_daily_streak:
                        longest_daily_streak = current
                else:
                    current = 0

            # current streak (ending at most recent day)
            for r in reversed(daily_rounds_sorted):
                if r.won:
                    daily_streak += 1
                else:
                    break

            average_daily_guesses = int(sum(r.guesses for r in daily_rounds) / len(daily_rounds))
            average_daily_time = (
                sum(r.time_to_complete_in_seconds for r in daily_rounds)/ len(daily_rounds))
        else:
            average_daily_guesses = 0
            average_daily_time = 0.0

        longest_survival_streak = 0
        for r in survival_rounds:
            if r.survival_streak > longest_survival_streak:
                longest_survival_streak = r.survival_streak

        score = longest_survival_streak + longest_daily_streak

        return LeaderboardStats(user_id=user_id,
                                daily_streak=daily_streak,
                                longest_daily_streak=longest_daily_streak,
                                average_daily_guesses=average_daily_guesses,
                                average_daily_time=average_daily_time,
                                longest_survival_streak=longest_survival_streak,
                                score=score)
        
        
