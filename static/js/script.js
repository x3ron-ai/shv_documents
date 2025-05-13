let blockCount = 0;
const dropZone = document.getElementById('dropZone');
const toc = document.getElementById('toc');
let isDropping = false;

function drag(event) {
    event.dataTransfer.setData("text", event.target.getAttribute('data-type'));
}

function dragBlock(event) {
    event.dataTransfer.setData("text", event.target.id);
    event.target.classList.add('dragging');
}

function allowDrop(event) {
    event.preventDefault();
    const target = event.target.closest('.block') || dropZone;
    const rect = target.getBoundingClientRect();
    const y = event.clientY;

    document.querySelectorAll('.block.insert-before, .block.insert-after, .drop-zone.insert-before')
        .forEach(el => el.classList.remove('insert-before', 'insert-after'));

    if (target === dropZone && dropZone.children.length === 0) {
        dropZone.classList.add('insert-before');
    } else if (target.classList.contains('block')) {
        if (y < rect.top + rect.height / 2) {
            target.classList.add('insert-before');
        } else {
            target.classList.add('insert-after');
        }
    }
}

function drop(event) {
    event.preventDefault();
    event.stopPropagation();
    if (isDropping) return;
    isDropping = true;

    document.querySelectorAll('.block.insert-before, .block.insert-after, .drop-zone.insert-before')
        .forEach(el => el.classList.remove('insert-before', 'insert-after'));

    const data = event.dataTransfer.getData("text");
    console.log(`Dropped type: ${data}`);
    
    let targetElement = event.target.closest('.block');
    const isDropZone = event.target === dropZone || event.target.closest('#dropZone') === dropZone;
    const rect = targetElement ? targetElement.getBoundingClientRect() : null;
    const y = event.clientY;

    document.querySelectorAll('.block.drag-over').forEach(el => el.classList.remove('drag-over'));

    if (data.startsWith('block_')) {
        const block = document.getElementById(data);
        if (block === targetElement) {
            isDropping = false;
            return;
        }
        if (isDropZone && !targetElement) {
            dropZone.appendChild(block);
        } else if (targetElement) {
            if (y < rect.top + rect.height / 2) {
                targetElement.parentNode.insertBefore(block, targetElement);
            } else {
                targetElement.parentNode.insertBefore(block, targetElement.nextSibling);
            }
        }
        updateTOC();
        saveTemplate();
    } else {
        const block = addBlock(data);
        if (isDropZone && !targetElement) {
            dropZone.appendChild(block);
        } else if (targetElement) {
            if (y < rect.top + rect.height / 2) {
                targetElement.parentNode.insertBefore(block, targetElement);
            } else {
                targetElement.parentNode.insertBefore(block, targetElement.nextSibling);
            }
        }
        updateTOC();
        saveTemplate();
    }
    isDropping = false;
}

function validateListNumber(input) {
    const value = input.value;
    if (!/^\d+(\.\d+)*$/.test(value)) {
        input.classList.add('invalid');
    } else {
        input.classList.remove('invalid');
        saveTemplate();
    }
}

function addBlock(type, parentId = null, itemId = null) {
    const block = document.createElement('div');
    block.className = 'block';
    block.draggable = true;
    block.id = `block_${blockCount++}`;
    block.ondragstart = dragBlock;
    block.ondragover = allowDrop;
    block.ondrop = drop;
    block.ondragend = () => block.classList.remove('dragging');

    let html = `<input type="hidden" name="block_type[]" value="${type}">`;
    console.log(`Adding block of type: ${type}, id: ${block.id}`);
    
    if (type === 'text') {
        const contentIdx = blockCount - 1;
        html += `
            <div class="contenteditable" contenteditable="true" style="font-family: 'Times New Roman'; font-size: 14px;"></div>
            <input type="hidden" name="content[]" id="content_${block.id}">
            <input type="hidden" name="align[]" value="justify" id="align_${block.id}">
            <input type="hidden" name="indent_left[]" value="0" id="indent_left_${block.id}">
            <input type="hidden" name="indent_first_line[]" value="0" id="indent_first_line_${block.id}">
            <input type="hidden" name="line_spacing[]" value="1.5" id="line_spacing_${block.id}">
            <input type="hidden" name="face_block_${contentIdx}" id="face_${block.id}" value="Times New Roman">
            <input type="hidden" name="size_block_${contentIdx}" id="size_${block.id}" value="14">
            <div class="style-menu">
                <label>Размер: <input type="number" min="8" max="72" value="14" oninput="updateStyle('${block.id}', 'size', this.value); saveTemplate()"></label>
                <label>Шрифт: <select oninput="updateStyle('${block.id}', 'face', this.value); saveTemplate()">
                    <option value="Times New Roman" selected>Times New Roman</option>
                    <option value="Arial">Arial</option>
                    <option value="Calibri">Calibri</option>
                </select></label>
                <label>Выравнивание: <select oninput="updateStyle('${block.id}', 'align', this.value); saveTemplate()">
                    <option value="left">Слева</option>
                    <option value="center">По центру</option>
                    <option value="right">Справа</option>
                    <option value="justify" selected>По ширине</option>
                </select></label>
                <label>Отступ слева (см): <input type="number" min="0" step="0.01" value="0" class="indent-input" data-block-id="${block.id}" data-property="indent_left"></label>
                <label>Первая строка (см): <input type="number" min="0" step="0.01" value="0" class="indent-input" data-block-id="${block.id}" data-property="indent_first_line"></label>
                <label>Междустрочный: <input type="number" min="0.5" step="0.01" value="1.5" class="indent-input" data-block-id="${block.id}" data-property="line_spacing"></label>
            </div>
        `;
    } else if (type === 'list_item') {
        const contentIdx = blockCount - 1;
        html += `
            <div class="list-item-container">
                <input type="text" name="list_item_number[]" class="list-item-number" placeholder="Нумерация" pattern="\\d+(\\.\\d+)*" oninput="validateListNumber(this)">
                <div class="contenteditable" contenteditable="true" style="font-family: 'Times New Roman'; font-size: 14px;"></div>
            </div>
            <input type="hidden" name="content[]" id="content_${block.id}">
            <input type="hidden" name="align[]" value="justify" id="align_${block.id}">
            <input type="hidden" name="indent_left[]" value="0" id="indent_left_${block.id}">
            <input type="hidden" name="indent_first_line[]" value="0" id="indent_first_line_${block.id}">
            <input type="hidden" name="line_spacing[]" value="1.5" id="line_spacing_${block.id}">
            <input type="hidden" name="face_block_${contentIdx}" id="face_${block.id}" value="Times New Roman">
            <input type="hidden" name="size_block_${contentIdx}" id="size_${block.id}" value="14">
            <div class="style-menu">
                <label>Размер: <input type="number" min="8" max="72" value="14" oninput="updateStyle('${block.id}', 'size', this.value); saveTemplate()"></label>
                <label>Шрифт: <select oninput="updateStyle('${block.id}', 'face', this.value); saveTemplate()">
                    <option value="Times New Roman" selected>Times New Roman</option>
                    <option value="Arial">Arial</option>
                    <option value="Calibri">Calibri</option>
                </select></label>
                <label>Выравнивание: <select oninput="updateStyle('${block.id}', 'align', this.value); saveTemplate()">
                    <option value="left">Слева</option>
                    <option value="center">По центру</option>
                    <option value="right">Справа</option>
                    <option value="justify" selected>По ширине</option>
                </select></label>
                <label>Отступ слева (см): <input type="number" min="0" step="0.01" value="0" class="indent-input" data-block-id="${block.id}" data-property="indent_left"></label>
                <label>Первая строка (см): <input type="number" min="0" step="0.01" value="0" class="indent-input" data-block-id="${block.id}" data-property="indent_first_line"></label>
                <label>Междустрочный: <input type="number" min="0.5" step="0.01" value="1.5" class="indent-input" data-block-id="${block.id}" data-property="line_spacing"></label>
            </div>
        `;
    } else if (type === 'comment') {
        const contentIdx = blockCount - 1;
        html += `
            <div class="contenteditable" contenteditable="true" style="font-family: 'Times New Roman'; font-size: 14px; background-color: #f0f0f0; padding: 10px; border-left: 4px solid #ccc;"></div>
            <input type="hidden" name="content[]" id="content_${block.id}">
        `;
    } else if (type === 'table') {
        html += `
            <textarea name="content[]" placeholder="Имя,Возраст,Город\nИван,25,Москва" oninput="saveTemplate()"></textarea>
            <label>Ширина столбцов (см): <input type="text" name="col_widths" value="2,1,2" oninput="saveTemplate()"></label>
        `;
    } else if (type === 'image') {
        html += `
            <input type="file" name="image[]" accept="image/jpeg,image/png,image/gif,image/bmp" onchange="previewImage(this, '${block.id}')">
            <input type="hidden" name="image_path[]" id="image_path_${block.id}">
            <img id="preview_${block.id}" class="image-preview" style="display: none;">
            <label>Подпись: <input type="text" name="image_caption[]" id="caption_${block.id}" oninput="saveTemplate()"></label>
            <div class="style-menu">
                <label><input type="checkbox" name="caption_bold[]" onchange="saveTemplate()"> Жирный</label>
                <label>Размер: <input type="number" name="caption_size[]" min="8" max="72" value="12" onchange="saveTemplate()"></label>
                <label>Шрифт: <select name="caption_face[]" onchange="saveTemplate()">
                    <option value="Times New Roman" selected>Times New Roman</option>
                    <option value="Arial">Arial</option>
                    <option value="Calibri">Calibri</option>
                </select></label>
                <label>Цвет: <input type="color" name="caption_color[]" value="#000000" onchange="saveTemplate()"></label>
            </div>
        `;
    }

    html += `<button type="button" onclick="removeBlock('${block.id}')">Удалить</button>`;
    block.innerHTML = html;

    if (type === 'text' || type === 'list_item' || type === 'comment') {
        const editable = block.querySelector('.contenteditable');
        editable.addEventListener('input', () => {
            block.querySelector(`#content_${block.id}`).value = editable.innerHTML;
            updateTOC();
            saveTemplate();
        });
    }

    if (type === 'text' || type === 'list_item') {
        const indentInputs = block.querySelectorAll('.indent-input');
        indentInputs.forEach(input => {
            const blockId = input.dataset.blockId;
            const property = input.dataset.property;
            input.addEventListener('change', () => {
                updateIndent(blockId, property, input.value);
                saveTemplate();
            });
            input.addEventListener('input', (e) => {
                const oldValue = parseFloat(block.querySelector(`#${property}_${blockId}`).value) || 0;
                const newValue = parseFloat(e.target.value) || 0;
                if (Math.abs(newValue - oldValue) === parseFloat(e.target.step)) {
                    updateIndent(blockId, property, e.target.value);
                    saveTemplate();
                }
            });
        });
    }

    return block;
}

function removeBlock(blockId) {
    const block = document.getElementById(blockId);
    if (!block) return;

    block.classList.add('removing');

    const rect = block.getBoundingClientRect();
    const particleCount = 20;
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const x = rect.width * Math.random();
        const y = rect.height * Math.random();
        particle.style.left = `${x}px`;
        particle.style.top = `${y}px`;
        const tx = (Math.random() - 0.5) * 100;
        const ty = (Math.random() - 0.5) * 100;
        particle.style.setProperty('--tx', `${tx}px`);
        particle.style.setProperty('--ty', `${ty}px`);
        block.appendChild(particle);
    }

    setTimeout(() => {
        block.remove();
        updateTOC();
        saveTemplate();
    }, 800);
}

function updateStyle(blockId, property, value) {
    const block = document.getElementById(blockId);
    const editable = block.querySelector('.contenteditable');
    if (property === 'size') {
        editable.style.fontSize = `${value}px`;
        block.querySelector(`#size_${blockId}`).value = value;
    } else if (property === 'face') {
        editable.style.fontFamily = value;
        block.querySelector(`#face_${blockId}`).value = value;
    } else if (property === 'align') {
        editable.style.textAlign = value;
        block.querySelector(`#align_${blockId}`).value = value;
    }
    block.querySelector(`#content_${blockId}`).value = editable.innerHTML;
    updateTOC();
    saveTemplate();
}

function updateIndent(blockId, property, value) {
    const block = document.getElementById(blockId);
    const input = block.querySelector(`#${property}_${blockId}`);
    const styleInput = block.querySelector(`input[data-property="${property}"][data-block-id="${blockId}"]`);
    if (input && styleInput) {
        input.value = value;
        styleInput.value = value;
        const editable = block.querySelector('.contenteditable');
        if (editable) {
            if (property === 'indent_left') {
                editable.style.marginLeft = `${value * 10}px`;
            } else if (property === 'indent_first_line') {
                editable.style.textIndent = `${value * 10}px`;
            } else if (property === 'line_spacing') {
                editable.style.lineHeight = value;
            }
        }
    }
}

function previewImage(input, blockId) {
    const preview = document.getElementById(`preview_${blockId}`);
    const pathInput = document.getElementById(`image_path_${blockId}`);
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const maxSize = 10 * 1024 * 1024; // 10 МБ
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            alert('Недопустимый формат файла. Поддерживаются: JPEG, PNG, GIF, BMP.');
            input.value = '';
            return;
        }
        if (file.size > maxSize) {
            alert('Файл слишком большой. Максимальный размер: 10 МБ.');
            input.value = '';
            return;
        }
        const formData = new FormData();
        formData.append('image', file);
        fetch('/upload_image', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.path) {
                preview.src = data.path;
                preview.style.display = 'block';
                pathInput.value = data.path;
                saveTemplate();
            } else if (data.error) {
                alert(data.error);
                input.value = '';
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки изображения:', error);
            alert('Ошибка загрузки изображения');
            input.value = '';
        });
    }
}

function updateTOC() {
    toc.innerHTML = '';
    const blocks = dropZone.querySelectorAll('.block');
    let commentIndex = 1;
    blocks.forEach(block => {
        const blockType = block.querySelector('input[name="block_type[]"]').value;
        if (blockType === 'comment') {
            const content = block.querySelector('.contenteditable').innerText || `Комментарий ${commentIndex}`;
            const shortContent = content.length > 30 ? content.substring(0, 27) + '...' : content;
            const tocItem = document.createElement('div');
            tocItem.className = 'toc-item';
            tocItem.innerText = shortContent;
            tocItem.onclick = () => {
                block.scrollIntoView({ behavior: 'smooth', block: 'start' });
                block.classList.add('highlight');
                setTimeout(() => block.classList.remove('highlight'), 1000);
            };
            toc.appendChild(tocItem);
            commentIndex++;
        }
    });
}

let isSaving = false;
async function saveTemplate(docId = null) {
    if (isSaving) return;
    isSaving = true;
    try {
        const form = document.getElementById('docForm');
        const formData = new FormData(form);
        console.log('FormData before submit:');
        for (const [key, value] of formData.entries()) {
            console.log(`${key}: ${value}`);
        }
        const effectiveDocId = docId || document.getElementById('document').getAttribute('data-template-id') || '0';
        const response = await fetch(`/document/${effectiveDocId}`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            console.log(`Document saved successfully, doc_id: ${data.doc_id}`);
            if (effectiveDocId === '0' && data.doc_id !== '0') {
                const newUrl = `/document/${data.doc_id}`;
                window.history.replaceState({}, '', newUrl);
                document.getElementById('document').setAttribute('data-template-id', data.doc_id);
                document.querySelector('h1').textContent = `Редактирование документа #${data.doc_id}`;
                const titleInput = form.querySelector('input[name="title"]');
                const templateSelect = form.querySelector('select[name="template_id"]');
                if (titleInput) titleInput.parentElement.style.display = 'none';
                if (templateSelect) templateSelect.parentElement.style.display = 'none';
            }
        } else if (data.error) {
            console.error(`Save error: ${data.error}`);
            alert(`Ошибка сохранения: ${data.error}`);
        }
    } catch (error) {
        console.error('Error:', error);
    } finally {
        isSaving = false;
    }
}

dropZone.ondragover = allowDrop;
dropZone.ondrop = drop;

const docId = document.getElementById('document').getAttribute('data-template-id');
if (docId && docId !== '0') {
    fetch('/get_template/' + docId)
        .then(response => response.json())
        .then(data => {
            console.log('Loaded template data:', data);
            dropZone.innerHTML = '';
            blockCount = 0;
            data.blocks.forEach((type, blockIdx) => {
                const block = addBlock(type);
                dropZone.appendChild(block);
                if (type === 'text' || type === 'list_item') {
                    const editable = block.querySelector('.contenteditable');
                    editable.innerHTML = data.contents[blockIdx] || "";
                    block.querySelector(`#content_${block.id}`).value = data.contents[blockIdx] || "";
                    block.querySelector(`#align_${block.id}`).value = data.aligns[blockIdx] || 'justify';
                    block.querySelector(`select[oninput*="align"]`).value = data.aligns[blockIdx] || 'justify';
                    block.querySelector(`#indent_left_${block.id}`).value = data.indents_left[blockIdx] || '0';
                    block.querySelector(`input[data-property="indent_left"]`).value = data.indents_left[blockIdx] || '0';
                    block.querySelector(`#indent_first_line_${block.id}`).value = data.indents_first_line[blockIdx] || '0';
                    block.querySelector(`input[data-property="indent_first_line"]`).value = data.indents_first_line[blockIdx] || '0';
                    block.querySelector(`#line_spacing_${block.id}`).value = data.line_spacings[blockIdx] || '1.5';
                    block.querySelector(`input[data-property="line_spacing"]`).value = data.line_spacings[blockIdx] || '1.5';
                    block.querySelector(`#face_${block.id}`).value = data.font_faces[blockIdx] || 'Times New Roman';
                    editable.style.fontFamily = data.font_faces[blockIdx] || 'Times New Roman';
                    block.querySelector(`select[oninput*="face"]`).value = data.font_faces[blockIdx] || 'Times New Roman';
                    block.querySelector(`#size_${block.id}`).value = data.font_sizes[blockIdx] || '14';
                    editable.style.fontSize = `${data.font_sizes[blockIdx] || 14}px`;
                    block.querySelector(`input[oninput*="size"]`).value = data.font_sizes[blockIdx] || '14';
                    if (type === 'list_item' && blockIdx < data.list_item_numbers.length) {
                        block.querySelector('.list-item-number').value = data.list_item_numbers[blockIdx] || "1";
                    }
                } else if (type === 'comment') {
                    const editable = block.querySelector('.contenteditable');
                    editable.innerHTML = data.contents[blockIdx] || "";
                    block.querySelector(`#content_${block.id}`).value = data.contents[blockIdx] || "";
                } else if (type === 'table') {
                    block.querySelector('textarea').value = data.contents[blockIdx] || "";
                    block.querySelector('input[name="col_widths"]').value = data.col_widths || '2,1,2';
                } else if (type === 'image') {
                    block.querySelector(`#caption_${block.id}`).value = data.captions[blockIdx] || "";
                    if (data.paths[blockIdx]) {
                        block.querySelector(`#preview_${block.id}`).src = data.paths[blockIdx];
                        block.querySelector(`#preview_${block.id}`).style.display = 'block';
                        block.querySelector(`#image_path_${block.id}`).value = data.paths[blockIdx];
                    }
                }
            });
            updateTOC();
        })
        .catch(error => console.error('Ошибка загрузки документа:', error));
}

function updateDraggableState() {
    const isPortrait = window.innerWidth < window.innerHeight;
    const blocks = document.querySelectorAll('.block');
    blocks.forEach(block => {
        block.draggable = !isPortrait;
        if (isPortrait) {
            block.ondragstart = null;
        } else {
            block.ondragstart = dragBlock;
        }
    });
}

function updateDropZoneEvents() {
    const isPortrait = window.innerWidth < window.innerHeight;
    if (isPortrait) {
        dropZone.ondragover = null;
        dropZone.ondrop = null;
    } else {
        dropZone.ondragover = allowDrop;
        dropZone.ondrop = drop;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateDraggableState();
    updateDropZoneEvents();
});
window.addEventListener('resize', () => {
    updateDraggableState();
    updateDropZoneEvents();
});