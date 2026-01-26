from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import pyotp

load_dotenv()
import qrcode
import io
import base64
import json
import os
import time

app = Flask(__name__)
# Change this in production via Environment Variable
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')

# --- Configuration ---
# Admin Password
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD')
# TOTP Secret
FIXED_TOTP_SECRET = os.environ.get('TOTP_SECRET')

# GitHub Persistence Config
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPO_NAME = os.environ.get('GITHUB_REPO')

# Upload Config
UPLOAD_FOLDER_CERTS = os.path.join(app.root_path, 'static', 'uploads', 'certificates')
UPLOAD_FOLDER_DOCS = os.path.join(app.root_path, 'uploads', 'private')
UPLOAD_FOLDER_RESEARCH_PUBLIC = os.path.join(app.root_path, 'static', 'uploads', 'research_public')
UPLOAD_FOLDER_PROJECTS = os.path.join(app.root_path, 'static', 'uploads', 'projects')
UPLOAD_FOLDER_IMAGES = os.path.join(app.root_path, 'static', 'images')
UPLOAD_FOLDER_TESTIMONIALS = os.path.join(app.root_path, 'static', 'uploads', 'testimonials')
UPLOAD_FOLDER_LOGOS = os.path.join(app.root_path, 'static', 'uploads', 'logos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'txt'}

app.config['UPLOAD_FOLDER_CERTS'] = UPLOAD_FOLDER_CERTS
app.config['UPLOAD_FOLDER_DOCS'] = UPLOAD_FOLDER_DOCS
app.config['UPLOAD_FOLDER_RESEARCH_PUBLIC'] = UPLOAD_FOLDER_RESEARCH_PUBLIC
app.config['UPLOAD_FOLDER_RESEARCH_PUBLIC'] = UPLOAD_FOLDER_RESEARCH_PUBLIC
app.config['UPLOAD_FOLDER_PROJECTS'] = UPLOAD_FOLDER_PROJECTS

UPLOAD_FOLDER_TESTIMONIALS = os.path.join(app.root_path, 'static', 'uploads', 'testimonials')
app.config['UPLOAD_FOLDER_TESTIMONIALS'] = UPLOAD_FOLDER_TESTIMONIALS
os.makedirs(UPLOAD_FOLDER_TESTIMONIALS, exist_ok=True)

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER_CERTS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_DOCS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_RESEARCH_PUBLIC, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_PROJECTS, exist_ok=True)
UPLOAD_FOLDER_IMAGES = os.path.join(app.root_path, 'static', 'images')
app.config['UPLOAD_FOLDER_IMAGES'] = UPLOAD_FOLDER_IMAGES
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_LOGOS, exist_ok=True)

# --- Data Handling ---
DATA_FILE_CERTS = os.path.join(app.root_path, 'data', 'certificates.json')
DATA_FILE_DOCS = os.path.join(app.root_path, 'data', 'documents.json')
DATA_FILE_RESEARCH = os.path.join(app.root_path, 'data', 'research.json')
DATA_FILE_PROJECTS = os.path.join(app.root_path, 'data', 'projects.json')
DATA_FILE_PROFILE = os.path.join(app.root_path, 'data', 'profile.json')
DATA_FILE_EDUCATION = os.path.join(app.root_path, 'data', 'education.json')
DATA_FILE_EXPERIENCE = os.path.join(app.root_path, 'data', 'experience.json')
DATA_FILE_SKILLS = os.path.join(app.root_path, 'data', 'skills.json')
DATA_FILE_MESSAGES = os.path.join(app.root_path, 'data', 'messages.json')
DATA_FILE_HOME = os.path.join(app.root_path, 'data', 'home.json')
DATA_FILE_TESTIMONIALS = os.path.join(app.root_path, 'data', 'testimonials.json')

@app.route('/dashboard')
def dashboard_redirect():
    return redirect(url_for('admin'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper Functions ---


import subprocess

def sync_to_github(file_path=None, content_bytes=None, is_binary=False, message="Update data"):
    """
    Syncs changes to GitHub using system git commands.
    This is more reliable than PyGithub for this environment.
    """
    try:
        # 1. Add changes
        subprocess.run(["git", "add", "."], check=True, cwd=app.root_path)
        
        # 2. Commit
        # Use a generic message if multiple files, or specific if one
        commit_msg = message if message else "Update content via Admin Dashboard"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=app.root_path)
        
        # 3. Push
        result = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=app.root_path)
        
        if result.returncode == 0:
            print("Successfully pushed to GitHub.", flush=True)
            return True, "Synced to GitHub"
        else:
            print(f"Git Push Failed: {result.stderr}", flush=True)
            return False, f"Push Failed: {result.stderr}"

    except subprocess.CalledProcessError as e:
        # This often happens if 'nothing to commit', which is fine
        print(f"Git command failed (might be nothing to commit): {e}", flush=True)
        return True, "Local save ok"
    except Exception as e:
        print(f"Git Sync System Error: {e}", flush=True)
        return False, str(e)

def init_data_from_github():
    """
    Pulls critical data files from GitHub on startup.
    This handles persistence for ephemeral filesystems (like Render).
    """
    if not GITHUB_TOKEN or not GITHUB_REPO_NAME:
        print("Startup: No GitHub credentials found. Skipping data restore.", flush=True)
        return

    print("Startup: Attempting to pull data from GitHub...", flush=True)
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO_NAME)
        
        # List of data files to sync
        data_files = [
            'data/certificates.json',
            'data/projects.json',
            'data/education.json',
            'data/experience.json',
            'data/skills.json',
            'data/research.json',
            'data/testimonials.json',
            'data/home.json',
            'data/profile.json',
            'data/documents.json',
            'data/messages.json'
        ]

        for file_rel_path in data_files:
            try:
                local_path = os.path.join(app.root_path, file_rel_path)
                contents = repo.get_contents(file_rel_path)
                
                # Check if we need to update (simple overwrite strategy)
                # Ensure directory exists first
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                with open(local_path, 'wb') as f:
                    f.write(contents.decoded_content)
                print(f"Startup: Restored {file_rel_path} from GitHub.", flush=True)
            except GithubException as e:
                if e.status == 404:
                    print(f"Startup: {file_rel_path} not found on GitHub. Using local default.", flush=True)
                else:
                    print(f"Startup: Error pulling {file_rel_path}: {e}", flush=True)
            except Exception as e:
                print(f"Startup: System error pulling {file_rel_path}: {e}", flush=True)

    except Exception as e:
        print(f"Startup: Critical Error connecting to GitHub: {e}", flush=True)

# Run restoration on module load (typically startup)
init_data_from_github()

def load_json(filepath):
    if os.path.exists(filepath):
        # Cache busting - read fresh every time
        # (Though open() usually reads fresh from disk anyway)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    # Sync to GitHub
    success, msg = sync_to_github(filepath, message=f"Update {os.path.basename(filepath)}")
    if not success:
        try:
            # Flash warning only if in request context (simple check)
            if request:
                flash(f"Data saved locally but GitHub Sync failed: {msg}", 'warning')
        except:
            pass # Not in request context



def save_certificate(data):
    certs = load_json(DATA_FILE_CERTS)
    certs.insert(0, data)
    save_json(DATA_FILE_CERTS, certs)

def save_document(data):
    docs = load_json(DATA_FILE_DOCS)
    docs.insert(0, data)
    save_json(DATA_FILE_DOCS, docs)

def save_research(data):
    research = load_json(DATA_FILE_RESEARCH)
    research.insert(0, data)
    save_json(DATA_FILE_RESEARCH, research)

def save_project(data):
    projects = load_json(DATA_FILE_PROJECTS)
    projects.insert(0, data)
    save_json(DATA_FILE_PROJECTS, projects)

def save_profile(data):
    save_json(DATA_FILE_PROFILE, data)

def save_education(data):
    items = load_json(DATA_FILE_EDUCATION)
    items.insert(0, data)
    save_json(DATA_FILE_EDUCATION, items)

def save_experience(data):
    items = load_json(DATA_FILE_EXPERIENCE)
    items.insert(0, data)
    save_json(DATA_FILE_EXPERIENCE, items)

def save_skill(data):
    items = load_json(DATA_FILE_SKILLS)
    items.append(data)
    save_json(DATA_FILE_SKILLS, items)

def save_message(data):
    items = load_json(DATA_FILE_MESSAGES)
    items.insert(0, data)
    save_json(DATA_FILE_MESSAGES, items)

def save_home(data):
    save_json(DATA_FILE_HOME, data)

def save_testimonial(data):
    items = load_json(DATA_FILE_TESTIMONIALS)
    items.insert(0, data)
    save_testimonial_file(items)

def update_testimonial_data(data):
    items = load_json(DATA_FILE_TESTIMONIALS)
    for i, item in enumerate(items):
        if str(item['id']) == str(data['id']):
            items[i] = data
            break
    save_testimonial_file(items)

def save_testimonial_file(items):
    save_json(DATA_FILE_TESTIMONIALS, items)

def delete_item(item_id, item_type):
    if item_type == 'certificate':
        filepath = DATA_FILE_CERTS
        upload_folder = app.config['UPLOAD_FOLDER_CERTS']
    elif item_type == 'document':
        filepath = DATA_FILE_DOCS
        upload_folder = app.config['UPLOAD_FOLDER_DOCS']
    elif item_type == 'research':
        filepath = DATA_FILE_RESEARCH
        upload_folder = None # Logic handled specifically below because of mixed folders
    elif item_type == 'project':
        filepath = DATA_FILE_PROJECTS
        upload_folder = app.config['UPLOAD_FOLDER_PROJECTS']
    elif item_type == 'education':
        filepath = DATA_FILE_EDUCATION
        upload_folder = None
    elif item_type == 'experience':
        filepath = DATA_FILE_EXPERIENCE
        upload_folder = None
    elif item_type == 'skill':
        filepath = DATA_FILE_SKILLS
        upload_folder = None
    elif item_type == 'message':
        filepath = DATA_FILE_MESSAGES
        upload_folder = None
    elif item_type == 'testimonial':
        filepath = DATA_FILE_TESTIMONIALS
        upload_folder = app.config['UPLOAD_FOLDER_TESTIMONIALS']
    else:
        return False

    items = load_json(filepath)
    item_to_delete = next((item for item in items if str(item['id']) == str(item_id)), None)
    
    if item_to_delete:
        # Delete associated file if it exists and is a local file
        if item_type == 'certificate' and item_to_delete.get('image'):
             file_path = os.path.join(upload_folder, item_to_delete['image'])
             if os.path.exists(file_path):
                 os.remove(file_path)
        elif item_type == 'document' and item_to_delete.get('filename'):
             file_path = os.path.join(upload_folder, item_to_delete['filename'])
             if os.path.exists(file_path):
                 os.remove(file_path)
        elif item_type == 'project' and item_to_delete.get('image'):
             file_path = os.path.join(upload_folder, item_to_delete['image'])
             if os.path.exists(file_path):
                 os.remove(file_path)
        
        elif item_type == 'research':
             if item_to_delete.get('document'):
                 file_path = os.path.join(app.config['UPLOAD_FOLDER_DOCS'], item_to_delete['document'])
                 if os.path.exists(file_path):
                     os.remove(file_path)
             if item_to_delete.get('public_document'):
                 file_path = os.path.join(app.config['UPLOAD_FOLDER_RESEARCH_PUBLIC'], item_to_delete['public_document'])
                 if os.path.exists(file_path):
                     os.remove(file_path)
             if item_to_delete.get('public_document'):
                  file_path = os.path.join(app.config['UPLOAD_FOLDER_RESEARCH_PUBLIC'], item_to_delete['public_document'])
                  if os.path.exists(file_path):
                      os.remove(file_path)

        elif item_type == 'testimonial':
             if item_to_delete.get('image'):
                 file_path = os.path.join(upload_folder, item_to_delete['image'])
                 # Generic delete doesn't know about robust file check, but this is fine.
                 if os.path.exists(file_path):
                     os.remove(file_path)
        items = [item for item in items if str(item['id']) != str(item_id)]
        save_json(filepath, items)
        return True
    return False


# --- Auth Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# --- Routes ---

@app.route('/')
def index():
    home_data = load_json(DATA_FILE_HOME)
    # Fallback default if file is empty or missing
    if not home_data:
        home_data = {
            "hero_text_1": "Building",
            "hero_text_accent": "Digital Experiences",
            "hero_text_2": "That Matter.",
            "subtitle": "Full Stack Developer & UI/UX Enthusiast."
        }
    
    profile = load_json(DATA_FILE_PROFILE)
    education = load_json(DATA_FILE_EDUCATION)
    experience = load_json(DATA_FILE_EXPERIENCE)
    skills = load_json(DATA_FILE_SKILLS)
    testimonials = load_json(DATA_FILE_TESTIMONIALS)
    
    return render_template('index.html', 
                           home=home_data,
                           profile=profile,
                           education=education,
                           experience=experience,
                           skills=skills)


@app.route('/projects')
def projects():
    projects_data = load_json(DATA_FILE_PROJECTS)
    return render_template('projects.html', projects=projects_data)

@app.route('/project/<int:id>')
def project_detail(id):
    return render_template('project_detail.html', id=id)



@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        if name and email and message:
            new_message = {
                "id": len(load_json(DATA_FILE_MESSAGES)) + 1,
                "name": name,
                "email": email,
                "message": message,
                "date": "Now" # You might want to use datetime here
            }
            save_message(new_message)
            flash('Message Sent Successfully!', 'success')
            return redirect(url_for('contact'))
        else:
            flash('Please fill all fields', 'error')

    return render_template('contact.html', profile=load_json(DATA_FILE_PROFILE))

@app.route('/certifications')
def certifications():
    certs = load_json(DATA_FILE_CERTS)
    return render_template('certifications.html', certificates=certs)

@app.route('/testimonials')
def testimonials_page():
    testimonials_data = load_json(DATA_FILE_TESTIMONIALS)
    return render_template('testimonials.html', testimonials=testimonials_data)


@app.route('/research')
def research():
    research_items = load_json(DATA_FILE_RESEARCH)
    research_items = load_json(DATA_FILE_RESEARCH)
    return render_template('research.html', research=research_items)

RESEARCH_PASSWORD = "siddarth1722@5424"

@app.route('/research/protected/<int:id>', methods=['GET', 'POST'])
def protected_research(id):
    research_items = load_json(DATA_FILE_RESEARCH)
    item = next((item for item in research_items if item['id'] == id), None)
    
    if not item or not item.get('document'):
        flash('Document not found or access denied.', 'error')
        return redirect(url_for('research'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password == RESEARCH_PASSWORD:
            # Serve file
            return send_from_directory(app.config['UPLOAD_FOLDER_DOCS'], item['document'])
        else:
            flash('Incorrect Password', 'error')
            
    return render_template('research_login.html')

@app.route('/add_testimonial', methods=['POST'])
def add_testimonial():
    password = request.form.get('password')
    if password == "siddarthjt024":
        name = request.form.get('name')
        message = request.form.get('message')
        if name and message:
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Unique filename to prevent overwrites
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_TESTIMONIALS'], filename))
                    image_filename = filename

            new_testimonial = {
                "id": len(load_json(DATA_FILE_TESTIMONIALS)) + 1,
                "name": name,
                "message": message,
                "date": "Now",
                "image": image_filename
            }
            save_testimonial(new_testimonial)
            
            # Sync image to GitHub if exists
            if image_filename:
                 local_path = os.path.join(app.config['UPLOAD_FOLDER_TESTIMONIALS'], image_filename)
                 sync_to_github(local_path, is_binary=True, message=f"Add testimonial image: {image_filename}")

            return {'success': True}
    return {'success': False, 'message': 'Invalid Password'}

# --- Admin / Auth Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        otp_token = request.form.get('otp')
        
        # Verify Password
        # Verify Password
        if password == ADMIN_PASSWORD_HASH:
            # TOTP Verification (Re-enabled)
            totp = pyotp.TOTP(FIXED_TOTP_SECRET)
            if totp.verify(otp_token):
                user = User(1)
                login_user(user)
                return redirect(url_for('admin'))
            else:
                flash('Invalid QR Code / OTP', 'error')
        else:
            flash('Invalid Password', 'error')
            
    # Security: Do not expose QR code on public login page.
    # 2FA setup should be done internally by an authenticated admin.
    return render_template('login.html', qr_code=None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_cert':
            title = request.form.get('title')
            issuer = request.form.get('issuer')
            date = request.form.get('date')
            desc = request.form.get('description')
            
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    safe_filename = secure_filename(file.filename)
                    filename = f"cert_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_CERTS'], filename))
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_CERTS'], filename), is_binary=True, message=f"Upload Cert {filename}")
                    image_filename = filename

            new_cert = {
                "id": len(load_json(DATA_FILE_CERTS)) + 1,
                "title": title,
                "issuer": issuer,
                "date": date,
                "link": "#",
                "description": desc,
                "image": image_filename
            }
            save_certificate(new_cert)
            flash('Certificate Added Successfully!', 'success')
        
        elif action == 'add_doc':
            title = request.form.get('title')
            if 'document' in request.files:
                file = request.files['document']
                if file and file.filename != '':
                    safe_filename = secure_filename(file.filename)
                    filename = f"doc_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename))
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename), is_binary=True, message=f"Upload Doc {filename}")
                    
                    new_doc = {
                        "id": len(load_json(DATA_FILE_DOCS)) + 1,
                        "title": title,
                        "filename": filename,
                        "date": "2026-01-03" # Ideally dynamic date
                    }
                    save_document(new_doc)
                    flash('Document Uploaded Successfully!', 'success')
                else:
                    flash('No file selected', 'error')
                    
        elif action == 'add_research':
            type = request.form.get('type')
            title = request.form.get('title')
            desc = request.form.get('description')
            link = request.form.get('link') or '#'
            
            doc_filename = None
            if 'document' in request.files:
                file = request.files['document']
                if file and file.filename != '':
                    safe_filename = secure_filename(file.filename)
                    filename = f"research_private_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename))
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_DOCS'], filename), is_binary=True, message=f"Upload Research Doc {filename}")
                    doc_filename = filename

            new_research = {
                "id": len(load_json(DATA_FILE_RESEARCH)) + 1,
                "type": type,
                "title": title,
                "description": desc,
                "link": link,
                "link_text": "Read Paper" if type == 'published' else "View Project",
                "document": doc_filename
            }

            if 'public_document' in request.files:
                file = request.files['public_document']
                if file and file.filename != '':
                    safe_filename = secure_filename(file.filename)
                    filename = f"research_public_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_RESEARCH_PUBLIC'], filename))
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_RESEARCH_PUBLIC'], filename), is_binary=True, message=f"Upload Public Research Doc {filename}")
                    new_research['public_document'] = filename

            save_research(new_research)
            flash('Research Item Added!', 'success')
            
        elif action == 'add_project':
            title = request.form.get('title')
            desc = request.form.get('description')
            link = request.form.get('link') or '#'
            
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    safe_filename = secure_filename(file.filename)
                    filename = f"project_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_PROJECTS'], filename))
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_PROJECTS'], filename), is_binary=True, message=f"Upload Project {filename}")
                    image_filename = filename
                    
            new_project = {
                "id": len(load_json(DATA_FILE_PROJECTS)) + 1,
                "title": title,
                "description": desc,
                "link": link,
                "image": image_filename
            }
            save_project(new_project)
            flash('Project Added Successfully!', 'success')

        elif action == 'update_profile':
            name = request.form.get('name')
            email = request.form.get('email')
            linkedin = request.form.get('linkedin')
            github = request.form.get('github')
            twitter = request.form.get('twitter')
            bio = request.form.get('bio')
            
            profile = load_json(DATA_FILE_PROFILE)
            profile['name'] = name
            profile['email'] = email
            profile['linkedin'] = linkedin
            profile['github'] = github
            profile['twitter'] = twitter
            profile['phone'] = request.form.get('phone') 
            profile['bio'] = bio

            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename != '':
                    safe_filename = secure_filename(file.filename)
                    filename = f"profile_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    profile['image'] = filename
                    profile['profile_image'] = filename # Update both keys just in case
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename), is_binary=True, message="Update Profile Pic")

            if 'banner_image' in request.files:
                 file = request.files['banner_image']
                 if file and file.filename != '':
                    safe_filename = secure_filename(file.filename)
                    filename = f"banner_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    profile['banner_image'] = filename
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename), is_binary=True, message="Update Banner")

            # New Section Images
            for img_field in ['skills_image', 'education_image', 'experience_image']:
                if img_field in request.files:
                    file = request.files[img_field]
                    if file and file.filename != '':
                        safe_filename = secure_filename(file.filename)
                        # Prefix with field name and timestamp to prevent collisions and fix caching
                        filename = f"{img_field}_{int(time.time())}_{safe_filename}"
                        
                        file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                        profile[img_field] = filename
                        sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename), is_binary=True, message=f"Update {img_field}")
            save_json(DATA_FILE_PROFILE, profile)
            # Sync profile data logic is now inside save_json with flash
            flash('Profile Updated!', 'success')

        elif action == 'add_role':
            prefix = request.form.get('prefix')
            core = request.form.get('core')
            if prefix and core:
                profile = load_json(DATA_FILE_PROFILE)
                if 'roles' not in profile:
                    profile['roles'] = []
                profile['roles'].append({"prefix": prefix, "core": core})
                save_json(DATA_FILE_PROFILE, profile)
                flash('Role Added!', 'success')
            else:
                flash('Prefix and Text required', 'error')

        elif action == 'delete_role':
            index = int(request.form.get('index'))
            profile = load_json(DATA_FILE_PROFILE)
            if 'roles' in profile and 0 <= index < len(profile['roles']):
                profile['roles'].pop(index)
                save_json(DATA_FILE_PROFILE, profile)
                flash('Role Deleted!', 'success')
            else:
                flash('Invalid role index', 'error')

        elif action == 'add_education':
            school = request.form.get('school')
            degree = request.form.get('degree')
            date = request.form.get('date')
            
            new_edu = {
                "id": len(load_json(DATA_FILE_EDUCATION)) + 1,
                "school": school,
                "degree": degree,
                "date": date
            }
            save_education(new_edu)
            flash('Education Added!', 'success')

        elif action == 'add_experience':
            role = request.form.get('role')
            company = request.form.get('company')
            date = request.form.get('date')
            desc = request.form.get('description')
            
            new_exp = {
                "id": len(load_json(DATA_FILE_EXPERIENCE)) + 1,
                "role": role,
                "company": company,
                "date": date,
                "description": desc
            }
            save_experience(new_exp)
            flash('Experience Added!', 'success')

        elif action == 'add_skill':
            new_skill = {
                "id": len(load_json(DATA_FILE_SKILLS)) + 1,
                "category": request.form.get('category'),
                "skill_list": request.form.get('items')
            }
            save_skill(new_skill)
            flash('Skill Added!', 'success')

        elif action == 'add_testimonial':
            name = request.form.get('name')
            message = request.form.get('message')
            
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    safe_filename = secure_filename(file.filename)
                    filename = f"testimonial_{int(time.time())}_{safe_filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_TESTIMONIALS'], filename))
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_TESTIMONIALS'], filename), is_binary=True, message=f"Upload Testimonial Image {filename}")
                    image_filename = filename

            new_testimonial = {
                "id": len(load_json(DATA_FILE_TESTIMONIALS)) + 1,
                "name": name,
                "message": message,
                "date": "Now",
                "image": image_filename
            }
            save_testimonial(new_testimonial)
            flash('Testimonial Added!', 'success')

        elif action == 'update_testimonial':
            id = request.form.get('id')
            name = request.form.get('name')
            message = request.form.get('message')
            
            # Find existing to preserve or update image
            current_testimonials = load_json(DATA_FILE_TESTIMONIALS)
            existing_item = next((item for item in current_testimonials if str(item['id']) == str(id)), None)
            
            if existing_item:
                image_filename = existing_item.get('image')
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '' and allowed_file(file.filename):
                        safe_filename = secure_filename(file.filename)
                        filename = f"testimonial_{int(time.time())}_{safe_filename}"
                        file.save(os.path.join(app.config['UPLOAD_FOLDER_TESTIMONIALS'], filename))
                        sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_TESTIMONIALS'], filename), is_binary=True, message=f"Update Testimonial Image {filename}")
                        image_filename = filename

                updated_testimonial = {
                    "id": int(id),
                    "name": name,
                    "message": message,
                    "date": existing_item.get('date', "Now"),
                    "image": image_filename
                }
                update_testimonial_data(updated_testimonial)
                flash('Testimonial Updated!', 'success')
            else:
                flash('Testimonial not found', 'error')



        return redirect(url_for('admin'))
        
    documents = load_json(DATA_FILE_DOCS)
    certificates = load_json(DATA_FILE_CERTS)
    research = load_json(DATA_FILE_RESEARCH)
    projects_data = load_json(DATA_FILE_PROJECTS)
    profile = load_json(DATA_FILE_PROFILE)
    education = load_json(DATA_FILE_EDUCATION)
    experience = load_json(DATA_FILE_EXPERIENCE)
    skills = load_json(DATA_FILE_SKILLS)
    messages = load_json(DATA_FILE_MESSAGES)
    testimonials = load_json(DATA_FILE_TESTIMONIALS)
    home_data = load_json(DATA_FILE_HOME)
    return render_template('admin.html', 
                           documents=documents, 
                           certificates=certificates, 
                           research=research, 
                           projects=projects_data,
                           profile=profile,
                           education=education,
                           experience=experience,
                           skills=skills,
                           messages=messages,
                           testimonials=testimonials,
                           home=home_data)

@app.route('/admin/delete/<item_type>/<id>')
@login_required
def delete(item_type, id):
    if delete_item(id, item_type):
        flash(f'{item_type.capitalize()} deleted successfully', 'success')
    else:
        flash('Error deleting item', 'error')
    return redirect(url_for('admin'))

@app.route('/admin/download/<filename>')
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_DOCS'], filename)

@app.route('/googlecf8652954e7dc775.html')
def google_verification():
    return send_from_directory('static', 'googlecf8652954e7dc775.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)
