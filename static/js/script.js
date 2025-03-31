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
		event.target.appendChild(block);
		saveTemplate();
	} else {
		addBlock(data);
		saveTemplate();
	}
}

function dropBlock(event) {
	event.preventDefault();
	const blockId = event.dataTransfer.getData("text");
	const block = document.getElementById(blockId);
	const target = event.target.closest('.block') || dropZone;
	if (target !== block) {
		target.appendChild(block);
		saveTemplate();
	}
}

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
			<input type="hidden" name="face_block_${blockCount - 1}" id="face_${block.id}" value="Times New Roman">
			<input type="hidden" name="size_block_${blockCount - 1}" id="size_${block.id}" value="14">
			<div class="style-menu">
				<label>Жирный: <input type="checkbox" onchange="updateStyle('${block.id}', 'bold', this.checked); saveTemplate()"></label>
				<label>Размер: <input type="number" min="8" max="72" value="14" onchange="updateStyle('${block.id}', 'size', this.value); saveTemplate()"></label>
				<label>Шрифт: <select onchange="updateStyle('${block.id}', 'face', this.value); saveTemplate()">
					<option value="Times New Roman" selected>Times New Roman</option>
					<option value="Arial">Arial</option>
					<option value="Calibri">Calibri</option>
				</select></label>
				<label>Цвет: <input type="color" value="#000000" onchange="updateStyle('${block.id}', 'color', this.value.slice(1)); saveTemplate()"></label>
				<label>Выравнивание: <select onchange="updateStyle('${block.id}', 'align', this.value); saveTemplate()">
					<option value="left" selected>Слева</option>
					<option value="center">По центру</option>
					<option value="right">Справа</option>
					<option value="justify">По ширине</option>
				</select></label>
			</div>
		`;
	} else if (type === 'table') {
		html += `
			<textarea name="content[]" placeholder="Имя,Возраст,Город\nИван,25,Москва" oninput="saveTemplate()"></textarea>
			<label>Ширина столбцов: <input type="text" name="col_widths" value="2,1,2" oninput="saveTemplate()"></label>
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
			<img id="preview_${block.id}" class="image-preview" style="display: none; max-width: 100%; margin-top: 10px;">
			<label>Название картинки: <input type="text" name="image_caption[]" id="caption_${block.id}" placeholder="Введите название" oninput="saveTemplate()"></label>
			<div class="style-menu">
				<label>Жирный: <input type="checkbox" name="caption_bold[]" onchange="saveTemplate()"></label>
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

	html += `<button type="button" onclick="removeBlock('${block.id}'); saveTemplate()">Удалить</button>`;
	block.innerHTML = html;
	dropZone.appendChild(block);

	if (type === 'text') {
		const editable = block.querySelector('.contenteditable');
		editable.addEventListener('input', () => {
			const contentInput = block.querySelector(`#content_${block.id}`);
			contentInput.value = serializeContent(editable, block.id);
			saveTemplate();
		});
		const contentInput = block.querySelector(`#content_${block.id}`);
		contentInput.value = serializeContent(editable, block.id);
	}
}

function removeBlock(blockId) {
	const block = document.getElementById(blockId);
	block.remove();
}

function updateStyle(blockId, property, value) {
	const block = document.getElementById(blockId);
	const editable = block.querySelector('.contenteditable');
	const contentInput = block.querySelector(`#content_${blockId}`);
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
	contentInput.value = serializeContent(editable, blockId);
}

function serializeContent(editable, blockId) {
	let content = editable.innerHTML;
	const align = document.getElementById(`align_${blockId}`).value;
	return content;
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
			const imagePath = data.path;
			preview.src = imagePath;
			preview.style.display = 'block';
			pathInput.value = imagePath;
			saveTemplate();
		})
		.catch(error => console.error('Ошибка загрузки изображения:', error));
	}
}

function saveTemplate() {
	const formData = new FormData(document.getElementById('docForm'));
	fetch('/document/' + templateId, {
		method: 'POST',
		body: formData
	}).then(response => {
		if (!response.ok) {
			console.error('Ошибка сохранения шаблона');
		}
	}).catch(error => console.error('Ошибка:', error));
}

dropZone.ondragover = allowDrop;
dropZone.ondrop = drop;

document.querySelectorAll('.indent-options input').forEach(input => {
	input.addEventListener('input', saveTemplate);
});

// Логика загрузки шаблона
const templateId = document.getElementById('document').getAttribute('data-template-id');
if (templateId) {
	fetch('/get_template/' + templateId)
		.then(response => response.json())
		.then(data => {
			const firstTextIndex = data.blocks.indexOf("text") !== -1 ? data.blocks.indexOf("text") : 0;
			document.querySelector('input[name="indent_left"]').value = data.indents_left[firstTextIndex] || "0";
			document.querySelector('input[name="indent_first_line"]').value = data.indents_first_line[firstTextIndex] || "0";
			document.querySelector('input[name="line_spacing"]').value = data.line_spacings[firstTextIndex] || "1.5";

			data.blocks.forEach((type, index) => {
				addBlock(type);
				const block = document.getElementById(`block_${blockCount - 1}`);
				if (type === "text") {
					block.querySelector('.contenteditable').innerHTML = data.contents[index];
					block.querySelector(`#content_${block.id}`).value = data.contents[index];
					block.querySelector(`#align_${block.id}`).value = data.aligns[index];
					const alignSelect = block.querySelector(`select[onchange*="align"]`);
					if (alignSelect) {
						alignSelect.value = data.aligns[index];
					}
					const fontFace = data.font_faces && data.font_faces[index] ? data.font_faces[index] : "Times New Roman";
					const faceInput = block.querySelector(`#face_${block.id}`);
					if (faceInput) {
						faceInput.value = fontFace;
					}
					block.querySelector('.contenteditable').style.fontFamily = fontFace;
					const faceSelect = block.querySelector(`select[onchange*="face"]`);
					if (faceSelect) {
						faceSelect.value = fontFace;
					}
					const fontSize = data.font_sizes && data.font_sizes[index] ? data.font_sizes[index] : "14";
					const sizeInput = block.querySelector(`#size_${block.id}`);
					if (sizeInput) {
						sizeInput.value = fontSize;
					}
					block.querySelector('.contenteditable').style.fontSize = `${fontSize}px`;
					const sizeInputField = block.querySelector(`input[onchange*="size"]`);
					if (sizeInputField) {
						sizeInputField.value = fontSize;
					}
				} else if (type === "table") {
					block.querySelector('textarea').value = data.contents[index];
					block.querySelector('input[name="col_widths"]').value = data.col_widths;
				} else if (type === "numbered_list" || type === "bullet_list") {
					block.querySelector('textarea').value = data.contents[index];
				} else if (type === "image") {
					block.querySelector(`#caption_${block.id}`).value = data.captions[index];
					if (data.paths[index]) {
						block.querySelector(`#preview_${block.id}`).src = '/' + data.paths[index];
						block.querySelector(`#preview_${block.id}`).style.display = "block";
						block.querySelector(`#image_path_${block.id}`).value = data.paths[index];
					}
				}
			});
		})
		.catch(error => console.error('Ошибка загрузки шаблона:', error));
}
