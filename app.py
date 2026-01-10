from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import pyotp
import qrcode
import io
import base64
import json
import os
from github import Github, GithubException

app = Flask(__name__)
# Change this in production via Environment Variable
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')

# --- Configuration ---
# Admin Password (default 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD', 'admin') 
# TOTP Secret (default provided for demo, change in prod)
FIXED_TOTP_SECRET = os.environ.get('TOTP_SECRET', "JBSWY3DPEHPK3PXP") 

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper Functions ---

def sync_to_github(file_path, content_bytes=None, is_binary=False, message="Update data"):
    """
    Syncs a local file update to GitHub repository to ensure persistence.
    If content_bytes is provided, writes that. Otherwise reads from file_path.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO_NAME:
        print("GitHub Sync Skipped: Missing GITHUB_TOKEN or GITHUB_REPO")
        return

    try:
        g = Github(GITHUB_TOKEN)
        # Handle cases where repo name might include URL parts or just user/repo
        repo_name_clean = GITHUB_REPO_NAME.split('/')[-1] if '/' in GITHUB_REPO_NAME else GITHUB_REPO_NAME
        # If user provides user/repo, PyGithub get_repo handles it usually if authenticated user has access
        # Better: get_user().get_repo(name) gets it from user's repos.
        # SAFE WAY: g.get_repo(GITHUB_REPO_NAME) which works for 'user/repo' string
        repo = g.get_repo(GITHUB_REPO_NAME)
        
        # Calculate relative path from app root
        rel_path = os.path.relpath(file_path, app.root_path)

        if content_bytes is None:
            mode = 'rb' if is_binary else 'r'
            with open(file_path, mode) as f:
                content_bytes = f.read()

        try:
            # Try to get existing file
            contents = repo.get_contents(rel_path)
            repo.update_file(contents.path, f"{message} [skip ci]", content_bytes, contents.sha)
            print(f"Successfully synced {rel_path} to GitHub.")
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist, create it
                repo.create_file(rel_path, f"{message} [skip ci]", content_bytes)
                print(f"Created {rel_path} on GitHub.")
            else:
                print(f"Error syncing to GitHub: {e}")
    except Exception as e:
         print(f"GitHub Sync Error: {e}")

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)
    # Sync to GitHub
    sync_to_github(filepath, message=f"Update {os.path.basename(filepath)}")


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
        if password == ADMIN_PASSWORD_HASH:
            # Verify TOTP
            totp = pyotp.TOTP(FIXED_TOTP_SECRET)
            if totp.verify(otp_token):
                user = User(1)
                login_user(user)
                return redirect(url_for('admin'))
            else:
                flash('Invalid QR Code / OTP', 'error')
        else:
            flash('Invalid Password', 'error')
            
    # Generate QR Code for setup
    totp = pyotp.TOTP(FIXED_TOTP_SECRET)
    uri = totp.provisioning_uri(name="Siddarth Portfolio", issuer_name="Portfolio Admin")
    img = qrcode.make(uri)
    buffered = io.BytesIO()
    img.save(buffered)
    qr_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    return render_template('login.html', qr_code=qr_b64)

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
                    filename = secure_filename(file.filename)
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
                    # Allow secure filename for docs
                    filename = secure_filename(file.filename)
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
                    filename = secure_filename(file.filename)
                    # Saving to private docs folder
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
                    filename = secure_filename(file.filename)
                    # Saving to PUBLIC research folder
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
                    filename = secure_filename(file.filename)
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
            profile['bio'] = bio

            if 'profile_image' in request.files:
                file = request.files['profile_image']
                if file and file.filename != '':
                    filename = "profile_pic.png" # Keep it simple for now or use secure_filename
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                    # Sync? Profile pic is static/images/profile_pic.png usually.
                    # It's better to use text input for filename or keep fixed.
                    # For this user, let's just overwrite.
                    profile['image'] = filename
                    sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename), is_binary=True, message="Update Profile Pic")

            if 'banner_image' in request.files:
                 file = request.files['banner_image']
                 if file and file.filename != '':
                     filename = "banner.jpg"
                     file.save(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename))
                     sync_to_github(os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename), is_binary=True, message="Update Banner")

            save_json(DATA_FILE_PROFILE, profile)
            # Sync profile data
            sync_to_github(DATA_FILE_PROFILE, message="Update Profile Data")
            flash('Profile Updated!', 'success')

        elif action == 'add_education':
            school = request.form.get('school')
            degree = request.form.get('degree')
            date = request.form.get('date')
            
            logo_filename = None
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER_LOGOS, filename))
                    sync_to_github(os.path.join(UPLOAD_FOLDER_LOGOS, filename), is_binary=True, message=f"Upload Education Logo {filename}")
                    logo_filename = filename

            new_edu = {
                "id": len(load_json(DATA_FILE_EDUCATION)) + 1,
                "school": school,
                "degree": degree,
                "date": date,
                "logo": logo_filename
            }
            save_education(new_edu)
            flash('Education Added!', 'success')

        elif action == 'add_experience':
            role = request.form.get('role')
            company = request.form.get('company')
            date = request.form.get('date')
            desc = request.form.get('description')
            
            logo_filename = None
            if 'logo' in request.files:
                file = request.files['logo']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER_LOGOS, filename))
                    sync_to_github(os.path.join(UPLOAD_FOLDER_LOGOS, filename), is_binary=True, message=f"Upload Experience Logo {filename}")
                    logo_filename = filename

            new_exp = {
                "id": len(load_json(DATA_FILE_EXPERIENCE)) + 1,
                "role": role,
                "company": company,
                "date": date,
                "description": desc,
                "logo": logo_filename
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
                           home=home_data)

@app.route('/admin/delete/<item_type>/<int:id>')
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

if __name__ == '__main__':
    app.run(debug=True)
