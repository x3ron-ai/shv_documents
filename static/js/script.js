let blockCount = 0;
const dropZone = document.getElementById('dropZone');

function drag(event) {
    event.dataTransfer.setData("text", event.target.getAttribute('data-type'));
}

function dragBlock(event) {
    event.dataTransfer.setData("text", event.target.id);
    event.target.classList.add('dragging');
}

function allowDrop(event) {
    event.preventDefault();
}

function drop(event) {
    event.preventDefault();
    const data = event.dataTransfer.getData("text");
    if (data.startsWith('block_')) {
        const block = document.getElementById(data);
        event.target.closest('#dropZone').appendChild(block);
        saveTemplate();
    } else {
        addBlock(data);
        saveTemplate();
    }
}

function addBlock(type) {
    const block = document.createElement('div');
    block.className = 'block';
    block.draggable = true;
    block.id = `block_${blockCount++}`;
    block.ondragstart = dragBlock;
    block.ondragover = allowDrop;
    block.ondrop = drop;
    block.ondragend = () => block.classList.remove('dragging');

    let html = `<input type="hidden" name="block_type[]" value="${type}">`;
    
    if (type === 'text') {
        html += `
            <div class="contenteditable" contenteditable="true" style="font-family: 'Times New Roman'; font-size: 14px;"></div>
            <input type="hidden" name="content[]" id="content_${block.id}">
            <input type="hidden" name="align[]" value="justify" id="align_${block.id}">
            <input type="hidden" name="indent_left[]" value="0" id="indent_left_${block.id}">
            <input type="hidden" name="indent_first_line[]" value="0" id="indent_first_line_${block.id}">
            <input type="hidden" name="line_spacing[]" value="1.5" id="line_spacing_${block.id}">
            <input type="hidden" name="face_block_${blockCount - 1}" id="face_${block.id}" value="Times New Roman">
            <input type="hidden" name="size_block_${blockCount - 1}" id="size_${block.id}" value="14">
            <div class="style-menu">
                <label><input type="checkbox" onchange="updateStyle('${block.id}', 'bold', this.checked)"> Жирный</label>
                <label>Размер: <input type="number" min="8" max="72" value="14" onchange="updateStyle('${block.id}', 'size', this.value)"></label>
                <label>Шрифт: <select onchange="updateStyle('${block.id}', 'face', this.value)">
                    <option value="Times New Roman" selected>Times New Roman</option>
                    <option value="Arial">Arial</option>
                    <option value="Calibri">Calibri</option>
                </select></label>
                <label>Цвет: <input type="color" value="#000000" onchange="updateStyle('${block.id}', 'color', this.value.slice(1))"></label>
                <label>Выравнивание: <select onchange="updateStyle('${block.id}', 'align', this.value)">
                    <option value="left">Слева</option>
                    <option value="center">По центру</option>
                    <option value="right">Справа</option>
                    <option value="justify" selected>По ширине</option>
                </select></label>
                <label>Отступ слева (см): <input type="number" min="0" step="0.1" value="0" onchange="updateIndent('${block.id}', 'indent_left', this.value)"></label>
                <label>Первая строка (см): <input type="number" min="0" step="0.1" value="0" onchange="updateIndent('${block.id}', 'indent_first_line', this.value)"></label>
                <label>Междустрочный: <input type="number" min="0.5" step="0.1" value="1.5" onchange="updateIndent('${block.id}', 'line_spacing', this.value)"></label>
            </div>
        `;
    } else if (type === 'table') {
        html += `
            <textarea name="content[]" placeholder="Имя,Возраст,Город\nИван,25,Москва" oninput="saveTemplate()"></textarea>
            <label>Ширина столбцов (см): <input type="text" name="col_widths" value="2,1,2" oninput="saveTemplate()"></label>
        `;
    } else if (type === 'numbered_list' || type === 'bullet_list') {
        html += `
            <input type="hidden" name="list_type[]" value="${type === 'numbered_list' ? 'numbered' : 'bullet'}">
            <textarea name="content[]" placeholder="Элемент 1\nЭлемент 2" oninput="saveTemplate()"></textarea>
        `;
    } else if (type === 'image') {
        html += `
            <input type="file" name="image[]" accept="image/*" onchange="previewImage(this, '${block.id}')">
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
    dropZone.appendChild(block);

    if (type === 'text') {
        const editable = block.querySelector('.contenteditable');
        editable.addEventListener('input', () => {
            block.querySelector(`#content_${block.id}`).value = editable.innerHTML;
            saveTemplate();
        });
    }
}

function removeBlock(blockId) {
    document.getElementById(blockId).remove();
    saveTemplate();
}

function updateStyle(blockId, property, value) {
    const block = document.getElementById(blockId);
    const editable = block.querySelector('.contenteditable');
    if (property === 'bold') {
        editable.style.fontWeight = value ? 'bold' : 'normal';
    } else if (property === 'size') {
        editable.style.fontSize = `${value}px`;
        block.querySelector(`#size_${blockId}`).value = value;
    } else if (property === 'face') {
        editable.style.fontFamily = value;
        block.querySelector(`#face_${blockId}`).value = value;
    } else if (property === 'color') {
        editable.style.color = `#${value}`;
    } else if (property === 'align') {
        editable.style.textAlign = value;
        block.querySelector(`#align_${blockId}`).value = value;
    }
    block.querySelector(`#content_${blockId}`).value = editable.innerHTML;
    saveTemplate();
}

function updateIndent(blockId, property, value) {
    document.getElementById(`${property}_${blockId}`).value = value;
    saveTemplate();
}

function previewImage(input, blockId) {
    const preview = document.getElementById(`preview_${blockId}`);
    const pathInput = document.getElementById(`image_path_${blockId}`);
    if (input.files && input.files[0]) {
        const formData = new FormData();
        formData.append('image', input.files[0]);
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
            }
        })
        .catch(error => console.error('Ошибка загрузки изображения:', error));
    }
}

function saveTemplate() {
    const formData = new FormData(document.getElementById('docForm'));
    fetch('/document/' + docId, {
        method: 'POST',
        body: formData
    }).catch(error => console.error('Ошибка сохранения:', error));
}

dropZone.ondragover = allowDrop;
dropZone.ondrop = drop;

const docId = document.getElementById('document').getAttribute('data-template-id');
if (docId) {
    fetch('/get_template/' + docId)
        .then(response => response.json())
        .then(data => {
            data.blocks.forEach((type, index) => {
                addBlock(type);
                const block = document.getElementById(`block_${blockCount - 1}`);
                if (type === 'text') {
                    const editable = block.querySelector('.contenteditable');
                    editable.innerHTML = data.contents[index];
                    block.querySelector(`#content_${block.id}`).value = data.contents[index];
                    block.querySelector(`#align_${block.id}`).value = data.aligns[index];
                    block.querySelector(`select[onchange*="align"]`).value = data.aligns[index];
                    block.querySelector(`#indent_left_${block.id}`).value = data.indents_left[index];
                    block.querySelector(`input[onchange*="indent_left"]`).value = data.indents_left[index];
                    block.querySelector(`#indent_first_line_${block.id}`).value = data.indents_first_line[index];
                    block.querySelector(`input[onchange*="indent_first_line"]`).value = data.indents_first_line[index];
                    block.querySelector(`#line_spacing_${block.id}`).value = data.line_spacings[index];
                    block.querySelector(`input[onchange*="line_spacing"]`).value = data.line_spacings[index];
                    block.querySelector(`#face_${block.id}`).value = data.font_faces[index];
                    editable.style.fontFamily = data.font_faces[index];
                    block.querySelector(`select[onchange*="face"]`).value = data.font_faces[index];
                    block.querySelector(`#size_${block.id}`).value = data.font_sizes[index];
                    editable.style.fontSize = `${data.font_sizes[index]}px`;
                    block.querySelector(`input[onchange*="size"]`).value = data.font_sizes[index];
                } else if (type === 'table') {
                    block.querySelector('textarea').value = data.contents[index];
                    block.querySelector('input[name="col_widths"]').value = data.col_widths;
                } else if (type === 'numbered_list' || type === 'bullet_list') {
                    block.querySelector('textarea').value = data.contents[index];
                } else if (type === 'image') {
                    block.querySelector(`#caption_${block.id}`).value = data.captions[index];
                    if (data.paths[index]) {
                        block.querySelector(`#preview_${block.id}`).src = data.paths[index];
                        block.querySelector(`#preview_${block.id}`).style.display = 'block';
                        block.querySelector(`#image_path_${block.id}`).value = data.paths[index];
                    }
                }
            });
        })
        .catch(error => console.error('Ошибка загрузки документа:', error));
}
