const initialData = [
    { time: "08:00 AM - 09:00 AM", task: "Mathematics" },
    { time: "09:00 AM - 10:00 AM", task: "Physics" },
    { time: "10:00 AM - 10:30 AM", task: "Short Break ☕" },
    { time: "10:30 AM - 11:30 AM", task: "Computer Science" },
    { time: "11:30 AM - 12:30 PM", task: "Literature" },
    { time: "12:30 PM - 01:30 PM", task: "Lunch Break 🍱" },
    { time: "01:30 PM - 03:00 PM", task: "Lab Work / Project" }
];

const body = document.getElementById('timetable-body');
const addBtn = document.getElementById('add-row-btn');
const resetBtn = document.getElementById('reset-btn');

function loadData() {
    const saved = localStorage.getItem('tina-timetable');
    return saved ? JSON.parse(saved) : initialData;
}

function saveData(data) {
    localStorage.setItem('tina-timetable', JSON.stringify(data));
}

function renderRow(item, index) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td contenteditable="true" data-key="time" data-index="${index}">${item.time}</td>
        <td contenteditable="true" data-key="task" data-index="${index}">${item.task}</td>
        <td class="actions-col">
            <button class="delete-btn" onclick="deleteRow(${index})">🗑️</button>
        </td>
    `;
    
    // Auto-save on blur
    tr.querySelectorAll('[contenteditable]').forEach(cell => {
        cell.addEventListener('blur', (e) => {
            const index = e.target.dataset.index;
            const key = e.target.dataset.key;
            const data = loadData();
            data[index][key] = e.target.innerText;
            saveData(data);
        });
    });

    return tr;
}

function refreshTable() {
    body.innerHTML = '';
    const data = loadData();
    data.forEach((item, index) => {
        body.appendChild(renderRow(item, index));
    });
}

function deleteRow(index) {
    const data = loadData();
    data.splice(index, 1);
    saveData(data);
    refreshTable();
}

addBtn.addEventListener('click', () => {
    const data = loadData();
    data.push({ time: "New Time", task: "New Activity" });
    saveData(data);
    refreshTable();
});

resetBtn.addEventListener('click', () => {
    if(confirm('Reset timetable to defaults?')) {
        saveData(initialData);
        refreshTable();
    }
});

// Initial boot
refreshTable();
