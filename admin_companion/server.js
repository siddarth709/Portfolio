const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const multer = require('multer');
const cookieParser = require('cookie-parser');
const { exec } = require('child_process');

const app = express();
const PORT = 3001;

// --- Config ---
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'siddarth672429@A';
const SESSION_SECRET = 'admin_session_secret';

const DATA_DIR = path.join(__dirname, '../data');
const UPLOAD_DIRS = {
    'testimonials': path.join(__dirname, '../static/uploads/testimonials'),
    'projects': path.join(__dirname, '../static/uploads/projects'),
    'certificates': path.join(__dirname, '../static/uploads/certificates'),
    'images': path.join(__dirname, '../static/images')
};

// Ensure upload dirs exist
Object.values(UPLOAD_DIRS).forEach(dir => {
    require('fs').mkdirSync(dir, { recursive: true });
});

// Multer Config
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        const type = req.params.type;
        const dir = UPLOAD_DIRS[type] || UPLOAD_DIRS['images'];
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '_' + Math.round(Math.random() * 1E9);
        const sanitize = file.originalname.replace(/[^a-zA-Z0-9.]/g, '_');
        cb(null, type + '_' + uniqueSuffix + '_' + sanitize);
    }
});
const upload = multer({ storage: storage });


// --- Middleware ---
app.use(cors());
app.use(bodyParser.json());
app.use(cookieParser());
app.use(express.static('public'));
app.use('/static', express.static(path.join(__dirname, '../static')));


// Auth Middleware
const requireAuth = (req, res, next) => {
    if (req.cookies.admin_session === SESSION_SECRET) {
        next();
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
};

// --- Helper Functions ---
const getFilePath = (type) => {
    const map = {
        'projects': 'projects.json',
        'profile': 'profile.json',
        'experience': 'experience.json',
        'education': 'education.json',
        'skills': 'skills.json',
        'certificates': 'certificates.json',
        'home': 'home.json',
        'testimonials': 'testimonials.json',
        'research': 'research.json',
        'documents': 'documents.json',
        'messages': 'messages.json'
    };
    if (!map[type]) return null;
    return path.join(DATA_DIR, map[type]);
};

// ** Git Sync Function **
const syncToGit = (message) => {
    return new Promise((resolve) => {
        // 1. Add static/uploads (for images) and data/*.json
        // 2. Commit
        // 3. Push
        // We use 'git add .' to cover everything in the repo just in case, or be specific.
        // Being specific is safer but 'git add .' ensures images are caught.
        // Let's target the relevant folders to be safe.
        const cmd = `git add data/ static/uploads/ && git commit -m "${message}" && git push`;

        console.log(`Executing Git Sync: ${message}`);
        exec(cmd, { cwd: path.join(__dirname, '../') }, (error, stdout, stderr) => {
            if (error) {
                console.error(`Git Sync Error: ${error.message}`);
                resolve(false);
                return;
            }
            console.log(`Git Sync output: ${stdout}`);
            resolve(true);
        });
    });
};


// --- API Routes ---

app.post('/api/login', (req, res) => {
    const { password } = req.body;
    if (password === ADMIN_PASSWORD) {
        res.cookie('admin_session', SESSION_SECRET, { httpOnly: true, maxAge: 24 * 60 * 60 * 1000 });
        res.json({ success: true });
    } else {
        res.status(401).json({ error: 'Invalid Password' });
    }
});

app.get('/api/check-auth', (req, res) => {
    res.json({ authenticated: req.cookies.admin_session === SESSION_SECRET });
});

app.post('/api/logout', (req, res) => {
    res.clearCookie('admin_session');
    res.json({ success: true });
});

app.get('/api/all-data', requireAuth, async (req, res) => {
    try {
        const files = [
            'projects.json', 'profile.json', 'experience.json',
            'education.json', 'skills.json', 'certificates.json',
            'home.json', 'testimonials.json', 'research.json', 'messages.json'
        ];
        const data = {};
        for (const file of files) {
            const key = file.replace('.json', '');
            try {
                const content = await fs.readFile(path.join(DATA_DIR, file), 'utf8');
                data[key] = JSON.parse(content);
            } catch (err) {
                data[key] = (key === 'profile' || key === 'home') ? {} : [];
            }
        }
        res.json(data);
    } catch (err) {
        res.status(500).json({ error: 'Failed to load data' });
    }
});

app.post('/api/update/:type', requireAuth, async (req, res) => {
    const type = req.params.type;
    const newData = req.body;
    const filePath = getFilePath(type);

    if (!filePath) return res.status(400).json({ error: 'Invalid data type' });

    try {
        await fs.writeFile(filePath, JSON.stringify(newData, null, 4), 'utf8');

        // Trigger Sync
        syncToGit(`Update ${type} via Admin`);

        res.json({ success: true });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Failed to save data' });
    }
});

app.post('/api/upload/:type', requireAuth, upload.single('file'), (req, res) => {
    if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

    // Trigger Sync (Async: don't wait for it to respond to user)
    syncToGit(`Upload ${req.file.filename}`);

    res.json({ success: true, filename: req.file.filename, path: req.file.path });
});

app.listen(PORT, () => {
    console.log(`Admin Companion running at http://localhost:${PORT}`);
});
