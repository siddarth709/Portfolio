// --- State ---
let globalData = {};
let currentView = 'dashboard';
let currentEditId = null;

// --- DOM Elements ---
const views = {
    dashboard: document.getElementById('dashboard'),
    dynamic: document.getElementById('dynamicContent') // Used for all list views
};

// --- Config for Sections ---
const config = {
    projects: {
        title: 'Projects',
        grid: 'grid-cols-1 md:grid-cols-2',
        renderCard: (item) => `
            <div class="glass-card flex flex-col h-full group relative">
                <div class="h-40 bg-gray-900/50 rounded-lg mb-4 overflow-hidden relative border border-[--color-border]">
                    ${item.image ? `<img src="/static/uploads/projects/${item.image}" class="w-full h-full object-cover">` : '<div class="w-full h-full flex items-center justify-center text-gray-600"><i class="fas fa-image text-3xl"></i></div>'}
                </div>
                <h3 class="font-bold text-lg mb-1 text-white">${item.title}</h3>
                <p class="text-gray-400 text-sm mb-4 line-clamp-2">${item.description}</p>
                <div class="mt-auto flex gap-2">
                    <button onclick="openModal('edit', 'projects', ${item.id})" class="flex-1 bg-white/5 text-gray-300 py-2 rounded-lg hover:bg-[--color-accent] hover:text-black transition-colors text-sm font-bold uppercase tracking-wider">Edit</button>
                    <button onclick="deleteItem('projects', ${item.id})" class="text-red-400 hover:text-red-500 px-3 py-2"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `,
        fields: [
            { name: 'title', label: 'Title', type: 'text', required: true },
            { name: 'description', label: 'Description', type: 'textarea', required: true },
            { name: 'link', label: 'Link URL', type: 'text' },
            { name: 'image', label: 'Cover Image', type: 'file', accept: 'image/*' }
        ]
    },
    testimonials: {
        title: 'Testimonials',
        grid: 'grid-cols-1 md:grid-cols-3',
        renderCard: (item) => `
            <div class="glass-card text-center relative flex flex-col items-center">
                <div class="w-16 h-16 rounded-full bg-gray-800 overflow-hidden mb-3 border border-[--color-border]">
                    ${item.image ? `<img src="/static/uploads/testimonials/${item.image}" class="w-full h-full object-cover">` : '<div class="w-full h-full flex items-center justify-center text-gray-500"><i class="fas fa-user"></i></div>'}
                </div>
                <h3 class="font-bold text-white">${item.name}</h3>
                <p class="text-xs text-[--color-accent] mb-3 uppercase tracking-wide">${item.date || ''}</p>
                <p class="text-gray-400 text-sm italic mb-4">"${item.message}"</p>
                <div class="flex justify-center gap-3 mt-auto"> 
                    <button onclick="openModal('edit', 'testimonials', ${item.id})" class="text-[--color-accent] hover:text-white text-sm">Edit</button>
                    <button onclick="deleteItem('testimonials', ${item.id})" class="text-red-400 hover:text-red-500 text-sm">Delete</button>
                </div>
            </div>
        `,
        fields: [
            { name: 'name', label: 'Client Name', type: 'text', required: true },
            { name: 'message', label: 'Testimonial', type: 'textarea', required: true },
            { name: 'date', label: 'Date', type: 'text', placeholder: 'e.g. Oct 2025' },
            { name: 'image', label: 'Client Photo', type: 'file', accept: 'image/*' }
        ]
    },
    experience: {
        title: 'Experience',
        grid: 'grid-cols-1',
        renderCard: (item) => `
            <div class="glass-card flex justify-between items-center group">
                <div>
                    <h3 class="font-bold text-xl text-[--color-accent]">${item.company}</h3>
                    <p class="font-bold text-white text-lg">${item.role}</p>
                    <p class="text-sm text-gray-500 uppercase tracking-widest mt-1">${item.date}</p>
                </div>
                <div class="flex gap-2">
                    <button onclick="openModal('edit', 'experience', ${item.id})" class="btn-icon text-gray-400 hover:text-[--color-accent]"><i class="fas fa-pen"></i></button>
                    <button onclick="deleteItem('experience', ${item.id})" class="btn-icon text-gray-400 hover:text-red-500"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `,
        fields: [
            { name: 'company', label: 'Company', type: 'text', required: true },
            { name: 'role', label: 'Role', type: 'text', required: true },
            { name: 'date', label: 'Duration', type: 'text', required: true },
            { name: 'description', label: 'Description', type: 'textarea' }
        ]
    },
    education: {
        title: 'Education',
        grid: 'grid-cols-1',
        renderCard: (item) => `
            <div class="glass-card flex justify-between items-center group">
                <div>
                    <h3 class="font-bold text-lg text-white">${item.school}</h3>
                    <p class="font-medium text-[--color-accent]">${item.degree}</p>
                    <p class="text-sm text-gray-500 mt-1">${item.date}</p>
                </div>
                <div class="flex gap-2">
                    <button onclick="openModal('edit', 'education', ${item.id})" class="btn-icon text-gray-400 hover:text-[--color-accent]"><i class="fas fa-pen"></i></button>
                    <button onclick="deleteItem('education', ${item.id})" class="btn-icon text-gray-400 hover:text-red-500"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `,
        fields: [
            { name: 'school', label: 'School', type: 'text', required: true },
            { name: 'degree', label: 'Degree', type: 'text', required: true },
            { name: 'date', label: 'Year', type: 'text', required: true }
        ]
    },
    skills: {
        title: 'Skills',
        grid: 'grid-cols-1',
        renderCard: (item) => `
            <div class="glass-card">
                <div class="flex justify-between items-start mb-4">
                    <h3 class="font-bold text-lg text-[--color-accent] uppercase tracking-wider">${item.category}</h3>
                     <div class="flex gap-2">
                        <button onclick="openModal('edit', 'skills', ${item.id})" class="text-gray-500 hover:text-[--color-accent]"><i class="fas fa-pen"></i></button>
                        <button onclick="deleteItem('skills', ${item.id})" class="text-gray-500 hover:text-red-500"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
                <div class="flex flex-wrap gap-2">
                    ${item.skill_list ? item.skill_list.split(',').map(s => `<span class="bg-white/5 border border-white/10 text-gray-300 px-3 py-1 rounded-full text-xs uppercase tracking-wide font-bold">${s.trim()}</span>`).join('') : ''}
                </div>
            </div>
        `,
        fields: [
            { name: 'category', label: 'Category', type: 'text', required: true },
            { name: 'skill_list', label: 'Skills (Comma separated)', type: 'textarea', required: true }
        ]
    },
    certificates: {
        title: 'Certifications',
        grid: 'grid-cols-1 md:grid-cols-2',
        renderCard: (item) => `
            <div class="glass-card flex items-start gap-4 group">
                 <div class="w-16 h-16 rounded bg-gray-800 flex-shrink-0 overflow-hidden border border-[--color-border]">
                    ${item.image ? `<img src="/static/uploads/certificates/${item.image}" class="w-full h-full object-cover">` : '<div class="flex items-center justify-center h-full text-gray-500"><i class="fas fa-award"></i></div>'}
                 </div>
                 <div class="flex-1">
                    <h3 class="font-bold text-lg leading-tight mb-1 text-white">${item.title}</h3>
                    <p class="text-sm text-[--color-accent] mb-1 font-bold">${item.issuer} &bull; ${item.date}</p>
                 </div>
                 <button onclick="deleteItem('certificates', ${item.id})" class="text-red-400 hover:text-red-500"><i class="fas fa-trash"></i></button>
            </div>
        `,
        fields: [
            { name: 'title', label: 'Certificate Name', type: 'text', required: true },
            { name: 'issuer', label: 'Issuer', type: 'text', required: true },
            { name: 'date', label: 'Year', type: 'text', required: true },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'image', label: 'Certificate Image', type: 'file', accept: 'image/*' }
        ]
    },
    research: {
        title: 'Research',
        grid: 'grid-cols-1',
        renderCard: (item) => `
            <div class="glass-card group">
                <div class="flex justify-between items-start">
                     <div>
                        <h3 class="font-bold text-lg text-white mb-2">${item.title}</h3>
                        <p class="text-gray-400 text-sm mb-2">${item.publication || 'Publication'}</p>
                     </div>
                     <div class="flex gap-2">
                        <button onclick="openModal('edit', 'research', ${item.id})" class="text-gray-500 hover:text-[--color-accent]"><i class="fas fa-pen"></i></button>
                        <button onclick="deleteItem('research', ${item.id})" class="text-gray-500 hover:text-red-500"><i class="fas fa-trash"></i></button>
                     </div>
                </div>
                <p class="text-gray-500 text-sm line-clamp-2">${item.abstract}</p>
            </div>
        `,
        fields: [
            { name: 'title', label: 'Stats/Title', type: 'text', required: true },
            { name: 'publication', label: 'Publication/Venue', type: 'text' },
            { name: 'abstract', label: 'Abstract', type: 'textarea' },
            { name: 'link', label: 'DOI/Link', type: 'text' }
        ]
    },
    messages: {
        title: 'Messages',
        grid: 'grid-cols-1',
        renderCard: (item) => `
            <div class="glass-card">
                 <div class="flex justify-between items-start mb-2">
                    <h3 class="font-bold text-lg text-white">${item.name || 'Anonymous'}</h3>
                    <span class="text-xs text-gray-500">${item.timestamp || 'No Date'}</span>
                 </div>
                 <p class="text-[--color-accent] text-sm mb-2">${item.email || 'No Email'}</p>
                 <p class="text-gray-400 italic">"${item.message}"</p>
                 
                 <div class="mt-4 flex justify-end">
                    <button onclick="deleteItem('messages', ${item.id})" class="text-red-400 hover:text-red-500 text-sm uppercase font-bold tracking-wider">Delete</button>
                 </div>
            </div>
        `,
        fields: [] // Read only usually
    }
};

// --- Initialization ---
async function init() {
    // Check Auth
    try {
        const authRes = await fetch('/api/check-auth');
        const authData = await authRes.json();
        if (!authData.authenticated) {
            document.getElementById('loginOverlay').classList.remove('hidden');
        } else {
            document.getElementById('loginOverlay').classList.add('hidden');
            loadData();
        }
    } catch (e) { console.error("Auth check failed", e); }
}

// Login Handler
document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();
    const password = document.getElementById('loginPassword').value;
    const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });
    const data = await res.json();
    if (data.success) {
        document.getElementById('loginOverlay').classList.add('hidden');
        loadData();
    } else {
        document.getElementById('loginError').classList.remove('hidden');
    }
};

// Logout
window.logout = async () => {
    await fetch('/api/logout', { method: 'POST' });
    location.reload();
};


// --- Data Loading ---
async function loadData() {
    try {
        const res = await fetch('/api/all-data');
        if (res.status === 401) {
            document.getElementById('loginOverlay').classList.remove('hidden');
            return;
        }
        if (!res.ok) throw new Error(`Server Error: ${res.status}`);

        globalData = await res.json();

        if (globalData.error) throw new Error(globalData.error);

        router(currentView); // Fixed: was renderRouter
        updateStats();
    } catch (err) {
        console.error(err);
        Swal.fire({
            icon: 'error',
            title: 'Connection Lost',
            text: `Could not load data. (${err.message})`,
            background: '#111',
            color: '#fff',
            confirmButtonText: 'Retry',
            preConfirm: () => location.reload()
        });
    }
}

function updateStats() {
    // Inject Dashboard Stats
    const statsContainer = document.querySelector('#dashboard .grid');
    if (!statsContainer) return;
    statsContainer.innerHTML = `
        <div class="glass-card hover:border-[--color-accent] cursor-pointer" onclick="router('projects')">
            <div class="text-gray-400 text-xs uppercase font-bold mb-2 tracking-widest">Projects</div>
            <div class="text-4xl font-black text-white">${(globalData.projects || []).length}</div>
        </div>
        <div class="glass-card hover:border-[--color-accent] cursor-pointer" onclick="router('testimonials')">
            <div class="text-gray-400 text-xs uppercase font-bold mb-2 tracking-widest">Testimonials</div>
            <div class="text-4xl font-black text-[--color-accent]">${(globalData.testimonials || []).length}</div>
        </div>
        <div class="glass-card hover:border-[--color-accent] cursor-pointer" onclick="router('messages')">
            <div class="text-gray-400 text-xs uppercase font-bold mb-2 tracking-widest">Messages</div>
            <div class="text-4xl font-black text-green-500">${(globalData.messages || []).length}</div>
        </div>
    `;
}

// --- Routing/View Switching ---
window.router = (viewName) => {
    currentView = viewName;

    // Update Sidebar
    document.querySelectorAll('.sidebar-link').forEach(el => {
        el.classList.remove('active');
        if (el.dataset.target === viewName) el.classList.add('active');
    });

    if (viewName === 'dashboard') {
        views.dashboard.classList.remove('hidden');
        views.dynamic.classList.add('hidden');
    } else if (config[viewName]) {
        // Generic List View
        views.dashboard.classList.add('hidden');
        views.dynamic.classList.remove('hidden');
        renderSection(viewName);
    } else {
        // Fallback
        views.dashboard.classList.add('hidden');
        views.dynamic.classList.remove('hidden');
        renderSection(viewName);
    }
};

function renderSection(type) {
    const cfg = config[type] || { title: type, grid: 'grid-cols-1', renderCard: i => JSON.stringify(i), fields: [] };
    const items = globalData[type] || [];

    document.getElementById('pageTitle').textContent = cfg.title;
    document.getElementById('addBtn').style.display = cfg.fields.length > 0 ? 'flex' : 'none'; // Hide add if no config

    const listEl = document.getElementById('contentList');
    listEl.className = `grid gap-6 ${cfg.grid}`;
    listEl.innerHTML = items.map(item => cfg.renderCard(item)).join('');
}


// --- Modal & Form Handling ---
window.openModal = (mode, type = currentView, id = null) => {
    const modal = document.getElementById('modalOverlay');
    const form = document.getElementById('dynamicForm');
    const modalTitle = document.getElementById('modalTitle');
    const cfg = config[type];

    if (!cfg) return;

    modal.classList.remove('hidden');
    // Animate in
    const modalContent = modal.querySelector('.glass-card');
    modalContent.classList.remove('scale-90', 'opacity-0');
    modalContent.classList.add('scale-100', 'opacity-100');

    modalTitle.textContent = mode === 'add' ? `Add New ${cfg.title.slice(0, -1)}` : `Edit ${cfg.title.slice(0, -1)}`;

    currentEditId = id;
    const item = mode === 'edit' ? globalData[type].find(i => i.id === id) : {};

    // Generate Fields
    form.innerHTML = cfg.fields.map(field => {
        if (field.type === 'file') {
            return `
                <div>
                    <label class="block text-sm font-bold text-gray-400 mb-2 uppercase tracking-wide">${field.label}</label>
                    <div class="file-input-wrapper relative">
                         <input type="file" name="${field.name}" accept="${field.accept}" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer" onchange="this.nextElementSibling.innerHTML = '<i class=\\'fas fa-check text-green-400\\'></i> ' + (this.files[0]?.name || 'Click to Upload Image')">
                         <span class="text-gray-500 text-sm pointer-events-none transition-colors">${item[field.name] ? 'Current: ' + item[field.name] : '<i class="fas fa-cloud-upload-alt text-2xl mb-2"></i><br>Click to Upload Image'}</span>
                    </div>
                </div>
            `;
        }
        const val = item[field.name] || '';
        if (field.type === 'textarea') {
            return `<div><label class="block text-sm font-bold text-gray-400 mb-2 uppercase tracking-wide">${field.label}</label><textarea name="${field.name}" class="input-field min-h-[100px]" rows="3" ${field.required ? 'required' : ''}>${val}</textarea></div>`;
        }
        return `<div><label class="block text-sm font-bold text-gray-400 mb-2 uppercase tracking-wide">${field.label}</label><input type="${field.type}" name="${field.name}" value="${val}" class="input-field" ${field.required ? 'required' : ''}></div>`;
    }).join('');

    // Form Submit Handler
    form.onsubmit = async (e) => {
        e.preventDefault();

        // SweetAlert Loading
        Swal.fire({
            title: 'SYNCING...',
            text: 'Pushing changes to GitHub...',
            didOpen: () => Swal.showLoading(),
            background: '#111',
            color: '#fff',
            showConfirmButton: false,
            allowOutsideClick: false
        });

        const formData = new FormData(form);
        const newItem = { ...item }; // Start with existing

        // Handle File Uploads first
        for (const field of cfg.fields) {
            if (field.type === 'file') {
                const fileInput = form.querySelector(`input[name="${field.name}"]`);
                if (fileInput.files.length > 0) {
                    const uploadData = new FormData();
                    uploadData.append('file', fileInput.files[0]);
                    // Upload
                    const uploadRes = await fetch(`/api/upload/${type}`, { method: 'POST', body: uploadData });
                    const uploadResult = await uploadRes.json();
                    if (uploadResult.success) {
                        newItem[field.name] = uploadResult.filename;
                    }
                }
            } else {
                newItem[field.name] = formData.get(field.name);
            }
        }

        // Generate ID for new items
        if (mode === 'add') {
            newItem.id = Date.now();
        }

        // Update Local State
        let newList = globalData[type] || [];
        if (mode === 'add') {
            newList = [newItem, ...newList];
        } else {
            newList = newList.map(i => i.id === id ? newItem : i);
        }

        // Save to Server
        await saveToServer(type, newList);
        closeModal();
    };
};

window.closeModal = () => {
    document.getElementById('modalOverlay').classList.add('hidden');
};

window.deleteItem = async (type, id) => {
    const result = await Swal.fire({
        title: 'DELETE ITEM?',
        text: "This action cannot be undone.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#333',
        confirmButtonText: 'YES, DELETE',
        cancelButtonText: 'CANCEL',
        background: '#111',
        color: '#fff',
        iconColor: '#d33'
    });

    if (result.isConfirmed) {
        Swal.fire({
            title: 'DELETING...',
            didOpen: () => Swal.showLoading(),
            background: '#111',
            color: '#fff',
            showConfirmButton: false,
            allowOutsideClick: false
        });
        const newList = globalData[type].filter(i => i.id !== id);
        await saveToServer(type, newList);
    }
};

// --- Generic Save Helper ---
async function saveToServer(type, newData) {
    try {
        const res = await fetch(`/api/update/${type}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newData)
        });
        const result = await res.json();
        if (result.success) {
            globalData[type] = newData;
            renderSection(type);
            Swal.fire({
                icon: 'success',
                title: 'SYNC COMPLETE',
                text: 'Changes are live.',
                timer: 2000,
                showConfirmButton: false,
                background: '#111',
                color: '#fff',
                iconColor: '#00f0ff'
            });
        } else {
            Swal.fire({ icon: 'error', title: 'Error', text: 'Failed to save data', background: '#111', color: '#fff' });
        }
    } catch (e) {
        Swal.fire({ icon: 'error', title: 'Connection Error', text: 'Check your server', background: '#111', color: '#fff' });
    }
}

// --- Mobile Sidebar Logic ---
window.toggleSidebar = () => {
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('mobileBackdrop');

    if (sidebar.classList.contains('-translate-x-full')) {
        sidebar.classList.remove('-translate-x-full');
        backdrop.classList.remove('hidden');
    } else {
        sidebar.classList.add('-translate-x-full');
        backdrop.classList.add('hidden');
    }
};

window.toggleSidebarUI = () => {
    if (window.innerWidth < 768) {
        toggleSidebar();
    }
};

// Start
init();
