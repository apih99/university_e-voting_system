import os
import django
import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voting_system.settings')
django.setup()

from accounts.models import Faculty, User, Profile
from elections.models import Election, Candidate, Vote

def create_faculties():
    faculties = [
        {'name': 'Faculty of Engineering', 'max_winners': 3},
        {'name': 'Faculty of Science', 'max_winners': 3},
        {'name': 'Faculty of Medicine', 'max_winners': 3},
        {'name': 'Faculty of Arts', 'max_winners': 2},
        {'name': 'Faculty of Law', 'max_winners': 2},
    ]
    
    created_faculties = []
    for faculty_data in faculties:
        faculty, created = Faculty.objects.get_or_create(
            name=faculty_data['name'],
            defaults={'max_winners': faculty_data['max_winners']}
        )
        created_faculties.append(faculty)
        print(f"{'Created' if created else 'Retrieved'} faculty: {faculty.name}")
    return created_faculties

def create_users(faculties):
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@upnm.edu.my',
            'student_id': '00000000',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'is_verified': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        Profile.objects.get_or_create(user=admin_user)
        print("Created admin user")

    # Create regular users and candidates
    users = []
    for i in range(1, 21):  # Create 20 users
        faculty = faculties[i % len(faculties)]
        username = f'user{i:02d}'
        student_id = f'{20230000 + i}'
        role = 'candidate' if i <= 10 else 'voter'
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@student.upnm.edu.my',
                'student_id': student_id,
                'faculty': faculty,
                'role': role,
                'first_name': f'First{i}',
                'last_name': f'Last{i}',
                'is_verified': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            profile = Profile.objects.get_or_create(user=user)[0]
            if role == 'candidate':
                profile.bio = f'Bio for {username}'
                profile.personal_statement = f'Personal statement for {username}'
                profile.campaign_promises = f'Campaign promises for {username}'
                profile.is_general_candidate = (i <= 5)  # First 5 candidates are general candidates
                profile.save()
            print(f"Created {role}: {username}")
        users.append(user)
    return users

def create_elections():
    # Create past, current, and future elections
    now = timezone.now()
    
    # Past election
    past_election, created = Election.objects.get_or_create(
        title='Past MPP Election 2023',
        defaults={
            'description': 'Past election for testing',
            'start_date': now - datetime.timedelta(days=30),
            'end_date': now - datetime.timedelta(days=23),
            'is_active': False
        }
    )
    if created:
        print("Created past election")

    # Current election
    current_election, created = Election.objects.get_or_create(
        title='Current MPP Election 2024',
        defaults={
            'description': 'Current active election',
            'start_date': now - datetime.timedelta(days=2),
            'end_date': now + datetime.timedelta(days=5),
            'is_active': True
        }
    )
    if created:
        print("Created current election")

    # Future election
    future_election, created = Election.objects.get_or_create(
        title='Upcoming MPP Election 2024',
        defaults={
            'description': 'Future election for testing',
            'start_date': now + datetime.timedelta(days=30),
            'end_date': now + datetime.timedelta(days=37),
            'is_active': True
        }
    )
    if created:
        print("Created future election")

    return [past_election, current_election, future_election]

def create_candidates(users, elections):
    current_election = elections[1]  # Use current election
    candidates = []
    
    for user in users[:10]:  # First 10 users are candidates
        candidate, created = Candidate.objects.get_or_create(
            user=user,
            election=current_election,
            defaults={
                'position_type': 'general' if user.profile.is_general_candidate else 'faculty',
                'manifesto': f'Manifesto for {user.username}',
                'approved': True
            }
        )
        if created:
            print(f"Created candidate: {user.username}")
        candidates.append(candidate)
    return candidates

def create_votes(users, elections, candidates):
    current_election = elections[1]
    
    # Create votes for the current election
    for user in users[10:]:  # Voters (non-candidates)
        # Check if user has already voted
        if not Vote.objects.filter(voter=user, election=current_election).exists():
            # Get candidates from user's faculty
            faculty_candidates = [c for c in candidates if c.user.faculty == user.faculty and not c.user.profile.is_general_candidate]
            general_candidates = [c for c in candidates if c.user.profile.is_general_candidate]
            
            # Create vote
            vote = Vote.objects.create(
                voter=user,
                election=current_election
            )
            
            # Add random candidates (up to 3 faculty and 7 general)
            import random
            vote.faculty_candidates.set(random.sample(faculty_candidates, min(len(faculty_candidates), 3)))
            vote.general_candidates.set(random.sample(general_candidates, min(len(general_candidates), 7)))
            
            print(f"Created vote for: {user.username}")

def main():
    print("Starting database population...")
    faculties = create_faculties()
    users = create_users(faculties)
    elections = create_elections()
    candidates = create_candidates(users, elections)
    create_votes(users, elections, candidates)
    print("Database population completed!")

if __name__ == '__main__':
    main()
