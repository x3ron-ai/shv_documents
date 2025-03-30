let blockCount = 0;

function drag(event) {
    event.dataTransfer.setData("type", event.target.getAttribute("data-type"));
}

const dropZone = document.getElementById('dropZone');
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const type = e.dataTransfer.getData("type");
    if (type) addBlock(type);
});

function addBlock(type) {
    const block = document.createElement('div');
    block.className = 'block';
    block.draggable = true;
    block.id = `block_${blockCount++}`;
    block.ondragstart = dragBlock;
    block.ondragover = (e) => e.preventDefault();
    block.ondrop = dropBlock;
    block.ondragend = () => block.classList.remove('dragging');

    let html = `<input type="hidden" name="block_type[]" value="${type}">`;
    
    if (type === 'text') {
        html += `
            <div class="contenteditable" contenteditable="true" style="font-family: 'Times New Roman'; font-size: 14px;"></div>
            <input type="hidden" name="content[]" id="content_${block.id}">
            <input type="hidden" name="align[]" value="left" id="align_${block.id}">
            <div class="style-menu">
                <label>Жирный: <input type="checkbox" onchange="updateStyle('${block.id}', 'bold', this.checked)"></label>
                <label>Размер: <input type="number" min="8" max="72" value="14" onchange="updateStyle('${block.id}', 'size', this.value)"></label>
                <label>Шрифт: <select onchange="updateStyle('${block.id}', 'face', this.value)">
                    <option value="Times New Roman" selected>Times New Roman</option>
                    <option value="Arial">Arial</option>
                    <option value="Calibri">Calibri</option>
                </select></label>
                <label>Цвет: <input type="color" value="#000000" onchange="updateStyle('${block.id}', 'color', this.value.slice(1))"></label>
                <label>Выравнивание: <select onchange="updateStyle('${block.id}', 'align', this.value)">
                    <option value="left" selected>Слева</option>
                    <option value="center">По центру</option>
                    <option value="right">Справа</option>
                    <option value="justify">По ширине</option>
                </select></label>
            </div>
        `;
    } else if (type === 'table') {
        html += `
            <textarea name="content[]" placeholder="Имя,Возраст,Город\nИван,25,Москва"></textarea>
            <label>Ширина столбцов: <input type="text" name="col_widths" value="2,1,2"></label>
        `;
    } else if (type === 'numbered_list' || type === 'bullet_list') {
        html += `
            <input type="hidden" name="list_type[]" value="${type === 'numbered_list' ? 'numbered' : 'bullet'}">
            <textarea name="content[]" placeholder="Элемент 1\nЭлемент 2"></textarea>
        `;
    } else if (type === 'image') {
        html += `
            <input type="file" name="image[]" accept="image/*" onchange="previewImage(this, '${block.id}')">
        `;
    }

    html += `<button type="button" onclick="removeBlock('${block.id}')">Удалить</button>`;
    block.innerHTML = html;
    dropZone.appendChild(block);

    if (type === 'text') {
        const editable = block.querySelector('.contenteditable');
        editable.addEventListener('input', () => {
            const contentInput = block.querySelector(`#content_${block.id}`);
            contentInput.value = serializeContent(editable, block.id);
        });
        // Устанавливаем начальное значение для скрытого поля
        const contentInput = block.querySelector(`#content_${block.id}`);
        contentInput.value = serializeContent(editable, block.id);
    }
}

function serializeContent(editable, blockId) {
    const block = document.getElementById(blockId);
    const text = editable.textContent || '';
    const bold = block.querySelector('input[type="checkbox"]').checked ? ['<b>', '</b>'] : ['', ''];
    const size = block.querySelector('input[type="number"]').value;
    const face = block.querySelector('select:nth-of-type(1)').value;
    const color = block.querySelector('input[type="color"]').value.slice(1); // Убираем #

    // Формируем строку с тегами
    return text ? `<font size="${size}" face="${face}" color="${color}">${bold[0]}${text}${bold[1]}</font>` : '';
}

function rgbToHex(rgb) {
    const match = rgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (match) {
        return '#' + [match[1], match[2], match[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
    }
    return rgb;
}

function previewImage(input, blockId) {
    const block = document.getElementById(blockId);
    const file = input.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            block.dataset.preview = `<img src="${e.target.result}" style="max-width: 100%;">`;
        };
        reader.readAsDataURL(file);
    }
}

function showContextMenu(event, blockId) {
    const block = document.getElementById(blockId);
    const editable = block.querySelector('.contenteditable');
    const selection = window.getSelection();
    if (!selection.rangeCount || !editable.contains(selection.anchorNode)) return;

    const menu = block.querySelector('.context-menu');
    menu.style.display = 'block';
    menu.style.left = `${event.pageX}px`;
    menu.style.top = `${event.pageY}px`;
}

function applyFormat(blockId, property, value) {
    const block = document.getElementById(blockId);
    const editable = block.querySelector('.contenteditable');
    const selection = window.getSelection();
    if (!selection.rangeCount) return;

    const range = selection.getRangeAt(0);
    if (range.collapsed) return;

    const selectedText = range.toString();
    const span = document.createElement('span');
    span.textContent = selectedText;

    // Получаем текущие стили из предыдущего span, если есть
    const parentSpan = range.commonAncestorContainer.parentElement;
    if (parentSpan && parentSpan.nodeName === 'SPAN') {
        span.style.cssText = parentSpan.style.cssText; // Копируем существующие стили
    }

    // Применяем новое форматирование
    if (property === 'bold') {
        span.style.fontWeight = value ? 'bold' : 'normal';
    } else if (property === 'size') {
        span.style.fontSize = `${value}px`;
    } else if (property === 'face') {
        span.style.fontFamily = value;
    } else if (property === 'color') {
        span.style.color = `#${value}`;
    }

    range.deleteContents();
    range.insertNode(span);
    selection.removeAllRanges();

    const contentInput = block.querySelector(`#content_${blockId}`);
    contentInput.value = serializeContent(editable);
}


function dragBlock(event) {
    event.dataTransfer.setData("blockId", event.target.id);
    setTimeout(() => event.target.classList.add('dragging'), 0);
}

function dropBlock(event) {
    event.preventDefault();
    const draggedId = event.dataTransfer.getData("blockId");
    const draggedBlock = document.getElementById(draggedId);
    const dropTarget = event.target.closest('.block');
    
    if (!draggedBlock || !dropTarget || draggedBlock === dropTarget) {
        return;
    }

    const allBlocks = Array.from(dropZone.children);
    const draggedIndex = allBlocks.indexOf(draggedBlock);
    const targetIndex = allBlocks.indexOf(dropTarget);
    
    if (draggedIndex !== -1 && targetIndex !== -1) {
        if (draggedIndex < targetIndex) {
            dropZone.insertBefore(draggedBlock, dropTarget.nextSibling || null);
        } else {
            dropZone.insertBefore(draggedBlock, dropTarget);
        }
    }
}

function removeBlock(blockId) {
    document.getElementById(blockId).remove();
}

document.addEventListener('click', (e) => {
    const menus = document.querySelectorAll('.context-menu');
    menus.forEach(menu => {
        if (!menu.contains(e.target)) menu.style.display = 'none';
    });
});

function showPreview() {
    const modal = document.getElementById('previewModal');
    const previewContent = document.getElementById('previewContent');
    previewContent.innerHTML = '';

    const blocks = dropZone.children;
    for (let block of blocks) {
        const type = block.querySelector('input[name="block_type[]"]').value;
        if (type === 'text') {
            const editable = block.querySelector('.contenteditable');
            previewContent.innerHTML += `<div style="text-align: ${block.querySelector('input[name="align[]"]').value}">${editable.innerHTML}</div>`;
        } else if (type === 'table') {
            const content = block.querySelector('textarea').value;
            const rows = content.split('\n').filter(row => row.trim());
            let tableHtml = '<table>';
            rows.forEach(row => {
                tableHtml += '<tr>';
                row.split(',').forEach(cell => tableHtml += `<td>${cell.trim()}</td>`);
                tableHtml += '</tr>';
            });
            tableHtml += '</table>';
            previewContent.innerHTML += tableHtml;
        } else if (type === 'numbered_list' || type === 'bullet_list') {
            const content = block.querySelector('textarea').value;
            const items = content.split('\n').filter(item => item.trim());
            const listType = block.querySelector('input[name="list_type[]"]').value;
            let listHtml = listType === 'numbered' ? '<ol>' : '<ul>';
            items.forEach(item => listHtml += `<li>${item}</li>`);
            listHtml += listType === 'numbered' ? '</ol>' : '</ul>';
            previewContent.innerHTML += listHtml;
        } else if (type === 'image' && block.dataset.preview) {
            previewContent.innerHTML += block.dataset.preview;
        }
    }

    modal.style.display = 'block';
}

function closePreview() {
    document.getElementById('previewModal').style.display = 'none';
}

function updateStyle(blockId, property, value) {
    const block = document.getElementById(blockId);
    const editable = block.querySelector('.contenteditable');
    const contentInput = block.querySelector(`#content_${block.id}`);
    const alignInput = block.querySelector(`#align_${block.id}`);

    // Применяем стили к отображению в интерфейсе
    if (property === 'bold') {
        editable.style.fontWeight = value ? 'bold' : 'normal';
    } else if (property === 'size') {
        editable.style.fontSize = `${value}px`;
    } else if (property === 'face') {
        editable.style.fontFamily = value;
    } else if (property === 'color') {
        editable.style.color = `#${value}`;
    } else if (property === 'align') {
        editable.style.textAlign = value;
        alignInput.value = value; // Обновляем скрытое поле выравнивания
    }

    // Обновляем скрытое поле content[]
    contentInput.value = serializeContent(editable, blockId);
}
