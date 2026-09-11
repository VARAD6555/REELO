/* REELO front-end interactions.
 * Page navigation is now real server-rendered routing (see base.html /
 * app/main/routes.py) instead of JS show/hide panels, so this file only
 * handles small in-page widgets: modals and live form feedback.
 */

// --- Preview Lightbox Modal -------------------------------------------------
function openPreviewModal(title, imgUrl) {
    document.getElementById('previewTitle').innerText = title;
    document.getElementById('previewImg').src = imgUrl;
    document.getElementById('previewModal').classList.add('open');
}

function closePreviewModal() {
    document.getElementById('previewModal').classList.remove('open');
}

// --- Hire Modal --------------------------------------------------------------
let activeHireRate = 0;

function openHireModal(hireUrl, editorName, rate, rating) {
    activeHireRate = rate;
    document.getElementById('hireForm').setAttribute('action', hireUrl);
    document.getElementById('hireModalTitle').innerText = `Hire ${editorName} (${rating})`;
    document.getElementById('hireModalSubtitle').innerText =
        `Price: \u20b9${rate.toLocaleString('en-IN')} per short video. Money stays safe with REELO until approved.`;
    document.getElementById('hireQuantity').value = 1;
    updateModalTotal();
    document.getElementById('hireModalOverlay').classList.add('open');
}

function closeHireModal() {
    document.getElementById('hireModalOverlay').classList.remove('open');
}

function updateModalTotal() {
    const qty = parseInt(document.getElementById('hireQuantity').value) || 1;
    const total = qty * activeHireRate;
    document.getElementById('hireModalTotal').innerText =
        `Total: \u20b9${total.toLocaleString('en-IN')} for ${qty} short(s)`;
}

// --- Messaging: pressing Enter submits the send-message form ----------------
function handleImEnter(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('imSendForm').requestSubmit();
    }
}

// Close a modal when clicking its backdrop
document.addEventListener('click', function (e) {
    if (e.target.classList && e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
    }
});
