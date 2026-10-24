import json
from datetime import datetime, timezone
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import MetaData, Table

from app.core.database import engine, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def seed_demo_users(db: Session):
    logger.info("Seeding demo users...")
    
    users = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "role": "admin",
            "is_active": True
        },
        {
            "email": "recruiter@example.com",
            "password": "recruiter123",
            "role": "recruiter",
            "is_active": True
        }
    ]
    
    for u in users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            new_user = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                is_active=u["is_active"]
            )
            db.add(new_user)
            logger.info(f"Created user: {u['email']}")
        else:
            logger.info(f"User already exists: {u['email']}")
            
    db.commit()

def seed_demo_jobs(db: Session):
    logger.info("Seeding demo jobs...")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    jobs_table = metadata.tables.get('jobs')
    
    if jobs_table is None:
        logger.error("Jobs table not found! Run migrations first.")
        return
        
    # Check if jobs exist
    count = db.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
    if count > 0:
        logger.info(f"Jobs already exist (count: {count}). Skipping jobs seed.")
        return

    now = datetime.now(timezone.utc)
    
    jobs = [
        {
            "title": "Senior Software Engineer",
            "department": "Engineering",
            "description": "Looking for a senior engineer with Python and React experience.",
            "location": "Remote",
            "work_mode": "remote",
            "employment_type": "full-time",
            "min_experience": 5,
            "max_experience": 10,
            "required_education": "Bachelor's",
            "required_skills": json.dumps(["Python", "React", "SQL", "Docker"]),
            "preferred_skills": json.dumps(["AWS", "Kubernetes", "GraphQL"]),
            "screening_weights": json.dumps({"skills": 40, "experience": 40, "education": 20}),
            "status": "open",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "Product Manager",
            "department": "Product",
            "description": "Experienced product manager to lead our core product team.",
            "location": "New York, NY",
            "work_mode": "hybrid",
            "employment_type": "full-time",
            "min_experience": 3,
            "max_experience": 8,
            "required_education": "Bachelor's",
            "required_skills": json.dumps(["Agile", "Jira", "User Research", "Data Analysis"]),
            "preferred_skills": json.dumps(["Technical Background", "Design Thinking"]),
            "screening_weights": json.dumps({"skills": 50, "experience": 30, "education": 20}),
            "status": "open",
            "created_at": now,
            "updated_at": now
        },
        {
            "title": "UX Designer",
            "department": "Design",
            "description": "Creative UX designer to build intuitive user experiences.",
            "location": "San Francisco, CA",
            "work_mode": "hybrid",
            "employment_type": "full-time",
            "min_experience": 2,
            "max_experience": 5,
            "required_education": "Bachelor's",
            "required_skills": json.dumps(["Figma", "Prototyping", "User Testing", "Wireframing"]),
            "preferred_skills": json.dumps(["HTML/CSS", "Animation"]),
            "screening_weights": json.dumps({"skills": 60, "experience": 30, "education": 10}),
            "status": "open",
            "created_at": now,
            "updated_at": now
        }
    ]
    
    db.execute(jobs_table.insert(), jobs)
    db.commit()
    logger.info(f"Created {len(jobs)} demo jobs.")

def seed_demo_candidates(db: Session):
    logger.info("Seeding demo candidates...")
    metadata = MetaData()
    metadata.reflect(bind=engine)
    candidates_table = metadata.tables.get('candidates')
    
    if candidates_table is None:
        logger.error("Candidates table not found! Run migrations first.")
        return
        
    # Check if candidates exist
    count = db.execute(text("SELECT COUNT(*) FROM candidates")).scalar()
    if count > 0:
        logger.info(f"Candidates already exist (count: {count}). Skipping candidates seed.")
        return

    now = datetime.now(timezone.utc)
    
    candidates = []
    # Generate 20 candidates with varying skills
    tech_skills = ["Python", "React", "SQL", "Docker", "AWS", "Java", "C++", "TypeScript", "Node.js"]
    design_skills = ["Figma", "Sketch", "Prototyping", "User Research", "Adobe CC", "Wireframing"]
    pm_skills = ["Agile", "Scrum", "Jira", "Data Analysis", "Roadmapping", "A/B Testing"]
    
    for i in range(1, 22):
        role_type = i % 3
        
        if role_type == 0:
            skills = tech_skills[:4] + (["GraphQL"] if i % 2 == 0 else [])
            title = "Software Engineer"
        elif role_type == 1:
            skills = pm_skills[:4] + (["Product Strategy"] if i % 2 == 0 else [])
            title = "Product Manager"
        else:
            skills = design_skills[:4] + (["HTML/CSS"] if i % 2 == 0 else [])
            title = "UX Designer"
            
        candidates.append({
            "name": f"Demo Candidate {i}",
            "email": f"candidate{i}@example.com",
            "phone": f"+1555010{i:03d}",
            "location": ["Remote", "New York, NY", "San Francisco, CA"][i % 3],
            "skills": json.dumps(skills),
            "education": json.dumps([{"degree": "Bachelor's", "major": "Computer Science" if role_type == 0 else "Design", "school": "State University"}]),
            "experience": json.dumps([{"title": title, "company": f"Tech Co {i}", "years": (i % 5) + 2}]),
            "status": "new",
            "created_at": now,
            "updated_at": now
        })
        
    db.execute(candidates_table.insert(), candidates)
    db.commit()
    logger.info(f"Created {len(candidates)} demo candidates.")

def main_seed():
    logger.info("Starting database seeding...")
    db = SessionLocal()
    try:
        seed_demo_users(db)
        seed_demo_jobs(db)
        seed_demo_candidates(db)
        logger.info("Database seeding completed successfully.")
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main_seed()
