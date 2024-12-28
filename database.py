from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    full_name = Column(String)
    email = Column(String)
    profile_data = Column(String)  # JSON string containing resume data
    created_at = Column(DateTime, default=datetime.utcnow)
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")

class Package(Base):
    __tablename__ = 'packages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Float)
    applications_limit = Column(Integer)
    description = Column(String)

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    package_id = Column(Integer, ForeignKey('packages.id'))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    applications_used = Column(Integer, default=0)
    
    user = relationship("User", back_populates="subscription")
    package = relationship("Package")

class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    job_title = Column(String)
    company = Column(String)
    status = Column(String)  # pending, submitted, rejected, accepted
    applied_date = Column(DateTime, default=datetime.utcnow)
    cover_letter = Column(String)
    
    user = relationship("User", back_populates="applications")

class Database:
    def __init__(self):
        self.engine = create_engine(os.getenv('DATABASE_URL'))
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_user(self, telegram_id, full_name, email=None):
        user = User(telegram_id=telegram_id, full_name=full_name, email=email)
        self.session.add(user)
        self.session.commit()
        return user
    
    def get_user(self, telegram_id):
        return self.session.query(User).filter_by(telegram_id=telegram_id).first()
    
    def update_user_profile(self, telegram_id, profile_data):
        user = self.get_user(telegram_id)
        if user:
            user.profile_data = profile_data
            self.session.commit()
            return True
        return False
    
    def add_application(self, user_id, job_title, company, cover_letter):
        application = Application(
            user_id=user_id,
            job_title=job_title,
            company=company,
            status='submitted',
            cover_letter=cover_letter
        )
        self.session.add(application)
        self.session.commit()
        return application
    
    def get_user_applications(self, user_id):
        return self.session.query(Application).filter_by(user_id=user_id).all()
    
    def update_subscription(self, user_id, package_id):
        subscription = self.session.query(Subscription).filter_by(user_id=user_id).first()
        if subscription:
            subscription.package_id = package_id
            subscription.applications_used = 0
        else:
            subscription = Subscription(user_id=user_id, package_id=package_id)
            self.session.add(subscription)
        self.session.commit()
        return subscription
