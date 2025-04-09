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
    console.log(`Dropped type: ${data}`); // Отладка
    if (data.startsWith('block_')) {
        const block = document.getElementById(data);
        event.target.closest('#dropZone').appendChild(block);
        saveTemplate();
    } else {
        addBlock(data);
        setTimeout(saveTemplate, 0);
    }
}

function addBlock(type, parentId = null, itemId = null) {
    const block = document.createElement('div');
    block.className = 'block';
    block.draggable = true;
    block.id = `block_${blockCount++}`;
    block.ondragstart = dragBlock;
    block.ondragover = allowDrop;
    block.ondrop = parentId ? (e) => dropNested(e, parentId, itemId) : drop;
    block.ondragend = () => block.classList.remove('dragging');

    let html = `<input type="hidden" name="block_type[]" value="${type}">`;
    console.log(`Adding block of type: ${type}, id: ${block.id}`); // Отладка
    
    if (type === 'numbered_list') {
        html += `
            <div class="list-container">
                <div class="list-items" id="list_items_${block.id}"></div>
                <button type="button" onclick="addListItem('${block.id}')">Добавить элемент</button>
            </div>
        `;
    } else if (type === 'list_item') {
        html += `
            <input type="text" name="list_item_title[]" class="list-item-title" placeholder="Название элемента" oninput="saveTemplate()">
            <input type="hidden" name="list_item_parent_${blockCount - 1}" value="${parentId}">
            <div class="list-drop-zone" id="list_drop_${block.id}" ondragover="allowDrop(event)" ondrop="dropNested(event, '${parentId}', '${block.id}')"></div>
            <button type="button" onclick="removeBlock('${block.id}')">Удалить элемент</button>
        `;
    } else if (type === 'text') {
        const contentIdx = blockCount - 1;
        html += `
            <div class="contenteditable" contenteditable="true" style="font-family: 'Times New Roman'; font-size: 14px;"></div>
            <input type="hidden" name="content[]" id="content_${block.id}">
            ${parentId && itemId ? `<input type="hidden" name="content_parent_${contentIdx}" value="${itemId}">` : ''}
            <input type="hidden" name="align[]" value="justify" id="align_${block.id}">
            <input type="hidden" name="indent_left[]" value="0" id="indent_left_${block.id}">
            <input type="hidden" name="indent_first_line[]" value="0" id="indent_first_line_${block.id}">
            <input type="hidden" name="line_spacing[]" value="1.5" id="line_spacing_${block.id}">
            <input type="hidden" name="face_block_${contentIdx}" id="face_${block.id}" value="Times New Roman">
            <input type="hidden" name="size_block_${contentIdx}" id="size_${block.id}" value="14">
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

    if (parentId && itemId) {
        document.getElementById(`list_drop_${itemId}`).appendChild(block);
    } else if (parentId) {
        document.getElementById(`list_items_${parentId}`).appendChild(block);
    } else {
        dropZone.appendChild(block);
    }

    if (type === 'text') {
        const editable = block.querySelector('.contenteditable');
        editable.addEventListener('input', () => {
            block.querySelector(`#content_${block.id}`).value = editable.innerHTML;
            saveTemplate();
        });
    }
}

function addListItem(listId) {
    addBlock('list_item', listId);
    const listBlock = document.getElementById(listId);
    const itemBlock = listBlock.querySelector('.list-items').lastElementChild;
    const nestedBtn = document.createElement('button');
    nestedBtn.type = 'button';
    nestedBtn.textContent = 'Добавить вложенный текст';
    nestedBtn.onclick = () => {
        addBlock('text', listId, itemBlock.id);
        saveTemplate();
    };
    itemBlock.appendChild(nestedBtn);
    saveTemplate();
}

function removeBlock(blockId) {
    const block = document.getElementById(blockId);
    block.remove();
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

function dropNested(event, parentId, itemId) {
    event.preventDefault();
    const data = event.dataTransfer.getData("text");
    if (data.startsWith('block_')) {
        const block = document.getElementById(data);
        document.getElementById(`list_drop_${itemId}`).appendChild(block);
    } else {
        addBlock(data, parentId, itemId);
    }
    saveTemplate();
}

function saveTemplate(docId = null) {
    const form = document.getElementById('docForm');
    const formData = new FormData(form);
    console.log('FormData before submit:');
    for (const [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
    
    const effectiveDocId = docId || document.getElementById('document').getAttribute('data-template-id') || '0';
    fetch(`/document/${effectiveDocId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())  // Ожидаем JSON
    .then(data => {
        if (data.success) {
            console.log(`Document saved successfully, doc_id: ${data.doc_id}`);
            // Здесь можно добавить уведомление на странице, если нужно
        } else if (data.error) {
            console.error(`Save error: ${data.error}`);
            alert(`Ошибка сохранения: ${data.error}`);
        }
    })
    .catch(error => console.error('Error:', error));
}

dropZone.ondragover = allowDrop;
dropZone.ondrop = drop;

const docId = document.getElementById('document').getAttribute('data-template-id');
if (docId) {
    fetch('/get_template/' + docId)
        .then(response => response.json())
        .then(data => {
            console.log('Loaded template data:', data);
            let contentIdx = 0;
            let listItemIdx = 0;
            data.blocks.forEach((type, blockIdx) => {
                if (type === 'numbered_list') {
                    addBlock('numbered_list');
                    const block = document.getElementById(`block_${blockCount - 1}`);
                    while (listItemIdx < data.list_item_titles.length && (blockIdx + 1 >= data.blocks.length || data.blocks[blockIdx + 1] === 'list_item')) {
                        addListItem(block.id);
                        const itemBlock = document.getElementById(`block_${blockCount - 1}`);
                        itemBlock.querySelector('.list-item-title').value = data.list_item_titles[listItemIdx] || "";
                        blockIdx++;
                        while (blockIdx < data.blocks.length && data.blocks[blockIdx] === 'text' && data.content_parents && data.content_parents[contentIdx] === `block_${blockCount - 1}`) {
                            addBlock('text', block.id, itemBlock.id);
                            const nestedBlock = document.getElementById(`block_${blockCount - 1}`);
                            nestedBlock.querySelector('.contenteditable').innerHTML = data.contents[contentIdx] || "";
                            nestedBlock.querySelector(`#content_${nestedBlock.id}`).value = data.contents[contentIdx] || "";
                            nestedBlock.querySelector(`#align_${nestedBlock.id}`).value = data.aligns[contentIdx];
                            nestedBlock.querySelector(`select[onchange*="align"]`).value = data.aligns[contentIdx];
                            nestedBlock.querySelector(`#indent_left_${nestedBlock.id}`).value = data.indents_left[contentIdx];
                            nestedBlock.querySelector(`input[onchange*="indent_left"]`).value = data.indents_left[contentIdx];
                            nestedBlock.querySelector(`#indent_first_line_${nestedBlock.id}`).value = data.indents_first_line[contentIdx];
                            nestedBlock.querySelector(`input[onchange*="indent_first_line"]`).value = data.indents_first_line[contentIdx];
                            nestedBlock.querySelector(`#line_spacing_${nestedBlock.id}`).value = data.line_spacings[contentIdx];
                            nestedBlock.querySelector(`input[onchange*="line_spacing"]`).value = data.line_spacings[contentIdx];
                            nestedBlock.querySelector(`#face_${nestedBlock.id}`).value = data.font_faces[contentIdx];
                            nestedBlock.querySelector('.contenteditable').style.fontFamily = data.font_faces[contentIdx];
                            nestedBlock.querySelector(`select[onchange*="face"]`).value = data.font_faces[contentIdx];
                            nestedBlock.querySelector(`#size_${nestedBlock.id}`).value = data.font_sizes[contentIdx];
                            nestedBlock.querySelector('.contenteditable').style.fontSize = `${data.font_sizes[contentIdx]}px`;
                            nestedBlock.querySelector(`input[onchange*="size"]`).value = data.font_sizes[contentIdx];
                            contentIdx++;
                            blockIdx++;
                        }
                        listItemIdx++;
                    }
                } else {
                    addBlock(type);
                    const block = document.getElementById(`block_${blockCount - 1}`);
                    if (type === 'text') {
                        const editable = block.querySelector('.contenteditable');
                        editable.innerHTML = data.contents[contentIdx] || "";
                        block.querySelector(`#content_${block.id}`).value = data.contents[contentIdx] || "";
                        block.querySelector(`#align_${block.id}`).value = data.aligns[contentIdx];
                        block.querySelector(`select[onchange*="align"]`).value = data.aligns[contentIdx];
                        block.querySelector(`#indent_left_${block.id}`).value = data.indents_left[contentIdx];
                        block.querySelector(`input[onchange*="indent_left"]`).value = data.indents_left[contentIdx];
                        block.querySelector(`#indent_first_line_${block.id}`).value = data.indents_first_line[contentIdx];
                        block.querySelector(`input[onchange*="indent_first_line"]`).value = data.indents_first_line[contentIdx];
                        block.querySelector(`#line_spacing_${block.id}`).value = data.line_spacings[contentIdx];
                        block.querySelector(`input[onchange*="line_spacing"]`).value = data.line_spacings[contentIdx];
                        block.querySelector(`#face_${block.id}`).value = data.font_faces[contentIdx];
                        editable.style.fontFamily = data.font_faces[contentIdx];
                        block.querySelector(`select[onchange*="face"]`).value = data.font_faces[contentIdx];
                        block.querySelector(`#size_${block.id}`).value = data.font_sizes[contentIdx];
                        editable.style.fontSize = `${data.font_sizes[contentIdx]}px`;
                        block.querySelector(`input[onchange*="size"]`).value = data.font_sizes[contentIdx];
                        contentIdx++;
                    } else if (type === 'table') {
                        block.querySelector('textarea').value = data.contents[contentIdx] || "";
                        block.querySelector('input[name="col_widths"]').value = data.col_widths;
                        contentIdx++;
                    } else if (type === 'image') {
                        block.querySelector(`#caption_${block.id}`).value = data.captions[blockIdx] || "";
                        if (data.paths[blockIdx]) {
                            block.querySelector(`#preview_${block.id}`).src = data.paths[blockIdx];
                            block.querySelector(`#preview_${block.id}`).style.display = 'block';
                            block.querySelector(`#image_path_${block.id}`).value = data.paths[blockIdx];
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Ошибка загрузки документа:', error));
}