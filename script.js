class RobotActionTaggerWithDatasets {
    constructor() {
        this.images = [];
        this.currentFrame = 0;
        this.isPlaying = false;
        this.playInterval = null;
        this.playSpeed = 1;
        this.tags = [];
        this.selectedTag = null;
        this.fps = 10;
        this.currentMode = 'local'; // 'local' or 'dataset'
        this.currentDataset = null;
        this.currentSequence = null;
        this.sessionId = this.generateSessionId();
        this.apiBaseUrl = 'http://localhost:8001/api';

        this.initializeElements();
        this.bindEvents();
    }

    generateSessionId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    initializeElements() {
        // 기존 DOM 요소들
        this.elements = {
            // 모드 전환
            localModeBtn: document.getElementById('localModeBtn'),
            datasetModeBtn: document.getElementById('datasetModeBtn'),
            localMode: document.getElementById('localMode'),
            datasetMode: document.getElementById('datasetMode'),
            
            // 로컬 업로드 관련
            imageUpload: document.getElementById('imageUpload'),
            uploadBtn: document.getElementById('uploadBtn'),
            imageCount: document.getElementById('imageCount'),
            
            // 데이터셋 관련
            datasetName: document.getElementById('datasetName'),
            datasetSplit: document.getElementById('datasetSplit'),
            loadDatasetBtn: document.getElementById('loadDatasetBtn'),
            datasetInfo: document.getElementById('datasetInfo'),
            datasetMeta: document.getElementById('datasetMeta'),
            sequenceBrowser: document.getElementById('sequenceBrowser'),
            datasetError: document.getElementById('datasetError'),
            datasetMetaInfo: document.getElementById('datasetMetaInfo'),
            
            // 이미지 뷰어
            currentImage: document.getElementById('currentImage'),
            placeholder: document.getElementById('placeholder'),
            frameNumber: document.getElementById('frameNumber'),
            currentTime: document.getElementById('currentTime'),
            
            // 컨트롤
            playBtn: document.getElementById('playBtn'),
            prevBtn: document.getElementById('prevBtn'),
            nextBtn: document.getElementById('nextBtn'),
            speedSelect: document.getElementById('speedSelect'),
            
            // 타임라인
            timeline: document.getElementById('timeline'),
            timelineTrack: document.getElementById('timelineTrack'),
            frameIndicator: document.getElementById('frameIndicator'),
            tagsContainer: document.getElementById('tagsContainer'),
            timelineScale: document.getElementById('timelineScale'),
            addTagBtn: document.getElementById('addTagBtn'),
            
            // 태그 편집
            tagPanel: document.getElementById('tagPanel'),
            tagName: document.getElementById('tagName'),
            tagStart: document.getElementById('tagStart'),
            tagEnd: document.getElementById('tagEnd'),
            tagDescription: document.getElementById('tagDescription'),
            saveTagBtn: document.getElementById('saveTagBtn'),
            deleteTagBtn: document.getElementById('deleteTagBtn'),
            cancelTagBtn: document.getElementById('cancelTagBtn'),
            
            // 태그 목록
            tagListContainer: document.getElementById('tagListContainer'),
            
            // 데이터 관리
            exportBtn: document.getElementById('exportBtn'),
            importBtn: document.getElementById('importBtn'),
            importInput: document.getElementById('importInput'),
            saveToServerBtn: document.getElementById('saveToServerBtn')
        };
    }

    bindEvents() {
        // 모드 전환 이벤트
        this.elements.localModeBtn.addEventListener('click', () => {
            this.switchMode('local');
        });

        this.elements.datasetModeBtn.addEventListener('click', () => {
            this.switchMode('dataset');
        });

        // 로컬 업로드 이벤트
        this.elements.uploadBtn.addEventListener('click', () => {
            this.elements.imageUpload.click();
        });

        this.elements.imageUpload.addEventListener('change', (e) => {
            this.handleImageUpload(e.target.files);
        });

        // 데이터셋 이벤트
        this.elements.loadDatasetBtn.addEventListener('click', () => {
            this.loadDataset();
        });

        // 컨트롤 이벤트
        this.elements.playBtn.addEventListener('click', () => {
            this.togglePlay();
        });

        this.elements.prevBtn.addEventListener('click', () => {
            this.previousFrame();
        });

        this.elements.nextBtn.addEventListener('click', () => {
            this.nextFrame();
        });

        this.elements.speedSelect.addEventListener('change', (e) => {
            this.playSpeed = parseFloat(e.target.value);
        });

        // 타임라인 이벤트
        this.elements.timeline.addEventListener('click', (e) => {
            this.handleTimelineClick(e);
        });

        this.elements.addTagBtn.addEventListener('click', () => {
            this.addNewTag();
        });

        // 태그 편집 이벤트
        this.elements.saveTagBtn.addEventListener('click', () => {
            this.saveTag();
        });

        this.elements.deleteTagBtn.addEventListener('click', () => {
            this.deleteTag();
        });

        this.elements.cancelTagBtn.addEventListener('click', () => {
            this.cancelTagEdit();
        });

        // 데이터 관리 이벤트
        this.elements.exportBtn.addEventListener('click', () => {
            this.exportData();
        });

        this.elements.importBtn.addEventListener('click', () => {
            this.elements.importInput.click();
        });

        this.elements.importInput.addEventListener('change', (e) => {
            this.importData(e.target.files[0]);
        });

        this.elements.saveToServerBtn.addEventListener('click', () => {
            this.saveToServer();
        });

        // 키보드 이벤트
        document.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
    }

    switchMode(mode) {
        this.currentMode = mode;
        
        if (mode === 'local') {
            this.elements.localModeBtn.classList.add('active');
            this.elements.datasetModeBtn.classList.remove('active');
            this.elements.localMode.style.display = 'block';
            this.elements.datasetMode.style.display = 'none';
        } else {
            this.elements.localModeBtn.classList.remove('active');
            this.elements.datasetModeBtn.classList.add('active');
            this.elements.localMode.style.display = 'none';
            this.elements.datasetMode.style.display = 'block';
        }
    }

    async loadDataset() {
        const datasetName = this.elements.datasetName.value.trim();
        if (!datasetName) {
            this.showError('데이터셋 이름을 입력해주세요.');
            return;
        }

        try {
            this.elements.loadDatasetBtn.textContent = '로딩 중...';
            this.elements.loadDatasetBtn.disabled = true;
            this.hideError();

            // 데이터셋 정보 가져오기
            const response = await fetch(`${this.apiBaseUrl}/datasets/${encodeURIComponent(datasetName)}/info`);
            if (!response.ok) {
                throw new Error(`데이터셋 로드 실패: ${response.status}`);
            }

            const datasetInfo = await response.json();
            this.currentDataset = datasetInfo;

            // Split 옵션 업데이트
            this.updateSplitOptions(datasetInfo.splits);
            
            // 데이터셋 메타데이터 표시
            this.displayDatasetMeta(datasetInfo);
            
            // 첫 번째 split 자동 선택
            if (datasetInfo.splits.length > 0) {
                this.elements.datasetSplit.value = datasetInfo.splits[0];
                await this.loadSequences(datasetName, datasetInfo.splits[0]);
            }

        } catch (error) {
            this.showError(`데이터셋 로드 중 오류 발생: ${error.message}`);
        } finally {
            this.elements.loadDatasetBtn.textContent = '데이터셋 로드';
            this.elements.loadDatasetBtn.disabled = false;
        }
    }

    updateSplitOptions(splits) {
        this.elements.datasetSplit.innerHTML = '<option value="">Split 선택</option>';
        splits.forEach(split => {
            const option = document.createElement('option');
            option.value = split;
            option.textContent = split;
            this.elements.datasetSplit.appendChild(option);
        });

        // Split 변경 이벤트 추가
        this.elements.datasetSplit.onchange = () => {
            const selectedSplit = this.elements.datasetSplit.value;
            if (selectedSplit && this.currentDataset) {
                this.loadSequences(this.currentDataset.name, selectedSplit);
            }
        };
    }

    displayDatasetMeta(datasetInfo) {
        this.elements.datasetMeta.innerHTML = '';
        
        const metaItems = [
            { label: '데이터셋', value: datasetInfo.name },
            { label: 'Splits', value: datasetInfo.splits.join(', ') },
            { label: '총 행 수', value: Object.values(datasetInfo.num_rows).reduce((a, b) => a + b, 0) }
        ];

        metaItems.forEach(item => {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'meta-item';
            metaDiv.innerHTML = `
                <div class="meta-label">${item.label}</div>
                <div class="meta-value">${item.value}</div>
            `;
            this.elements.datasetMeta.appendChild(metaDiv);
        });

        this.elements.datasetInfo.classList.add('visible');
    }

    async loadSequences(datasetName, split) {
        try {
            this.elements.sequenceBrowser.innerHTML = '<div class="loading">시퀀스 로딩 중...</div>';
            
            // 처음 10개 시퀀스 로드
            const maxSequences = 20;
            this.elements.sequenceBrowser.innerHTML = '';

            for (let i = 0; i < maxSequences; i++) {
                try {
                    const sequenceDiv = document.createElement('div');
                    sequenceDiv.className = 'sequence-item';
                    sequenceDiv.innerHTML = `
                        <div class="sequence-thumb">로딩 중...</div>
                        <div class="sequence-index">시퀀스 ${i}</div>
                    `;
                    
                    sequenceDiv.addEventListener('click', () => {
                        this.selectSequence(datasetName, split, i);
                    });
                    
                    this.elements.sequenceBrowser.appendChild(sequenceDiv);

                    // 비동기로 썸네일 로드
                    this.loadSequenceThumbnail(datasetName, split, i, sequenceDiv);
                } catch (error) {
                    // 해당 인덱스에 데이터가 없으면 중단
                    break;
                }
            }

        } catch (error) {
            this.elements.sequenceBrowser.innerHTML = `<div class="error">시퀀스 로드 실패: ${error.message}</div>`;
        }
    }

    async loadSequenceThumbnail(datasetName, split, index, sequenceDiv) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/datasets/${encodeURIComponent(datasetName)}/${split}/sequence/${index}`);
            if (!response.ok) return;

            const sequenceData = await response.json();
            if (sequenceData.images && sequenceData.images.length > 0) {
                const thumb = sequenceDiv.querySelector('.sequence-thumb');
                thumb.innerHTML = `<img src="data:image/png;base64,${sequenceData.images[0]}" style="max-width: 100%; max-height: 100%; object-fit: contain;">`;
            }
        } catch (error) {
            // 썸네일 로드 실패는 무시
        }
    }

    async selectSequence(datasetName, split, index) {
        try {
            // 이전 선택 해제
            document.querySelectorAll('.sequence-item').forEach(item => {
                item.classList.remove('selected');
            });

            // 현재 선택 표시
            const selectedItem = document.querySelector(`.sequence-item:nth-child(${index + 1})`);
            if (selectedItem) {
                selectedItem.classList.add('selected');
            }

            // 시퀀스 데이터 로드
            this.elements.placeholder.textContent = '시퀀스 로딩 중...';
            
            const response = await fetch(`${this.apiBaseUrl}/datasets/${encodeURIComponent(datasetName)}/${split}/sequence/${index}`);
            if (!response.ok) {
                throw new Error(`시퀀스 로드 실패: ${response.status}`);
            }

            const sequenceData = await response.json();
            this.currentSequence = sequenceData;

            // 이미지 데이터 변환
            this.images = sequenceData.images.map((img, i) => ({
                dataUrl: `data:image/png;base64,${img}`,
                name: `frame_${i.toString().padStart(3, '0')}.png`
            }));

            this.currentFrame = 0;
            this.updateUI();
            this.updateImageCount();
            this.createTimelineScale();
            this.enableControls();

            // 메타데이터 표시
            this.updateDatasetMetaInfo(sequenceData.metadata);

        } catch (error) {
            this.showError(`시퀀스 선택 중 오류 발생: ${error.message}`);
        }
    }

    updateDatasetMetaInfo(metadata) {
        if (!metadata) return;
        
        const info = [];
        if (metadata.dataset_name) info.push(`데이터셋: ${metadata.dataset_name}`);
        if (metadata.split) info.push(`Split: ${metadata.split}`);
        if (metadata.index !== undefined) info.push(`인덱스: ${metadata.index}`);
        
        this.elements.datasetMetaInfo.textContent = info.join(' | ');
    }

    showError(message) {
        this.elements.datasetError.textContent = message;
        this.elements.datasetError.style.display = 'block';
    }

    hideError() {
        this.elements.datasetError.style.display = 'none';
    }

    async saveToServer() {
        try {
            const data = {
                tags: this.tags,
                totalFrames: this.images.length,
                fps: this.fps,
                exportTime: new Date().toISOString(),
                version: '1.0',
                datasetName: this.currentDataset?.name || null,
                splitName: this.elements.datasetSplit.value || null
            };

            const response = await fetch(`${this.apiBaseUrl}/tagging/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`저장 실패: ${response.status}`);
            }

            const result = await response.json();
            alert(`서버에 저장되었습니다. 세션 ID: ${this.sessionId}`);

        } catch (error) {
            alert(`서버 저장 중 오류 발생: ${error.message}`);
        }
    }

    // 기존 메서드들 (로컬 업로드, 재생 제어, 태깅 등)
    async handleImageUpload(files) {
        if (files.length === 0) return;

        const fileArray = Array.from(files).sort((a, b) => a.name.localeCompare(b.name));
        
        this.images = [];
        this.elements.imageCount.textContent = `${fileArray.length}개 이미지 로딩 중...`;

        for (let file of fileArray) {
            const dataUrl = await this.fileToDataUrl(file);
            this.images.push({
                dataUrl: dataUrl,
                name: file.name
            });
        }

        this.currentFrame = 0;
        this.updateUI();
        this.updateImageCount();
        this.createTimelineScale();
        this.enableControls();
        this.elements.datasetMetaInfo.textContent = '로컬 업로드 모드';
    }

    fileToDataUrl(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(file);
        });
    }

    updateUI() {
        if (this.images.length === 0) return;

        this.elements.currentImage.src = this.images[this.currentFrame].dataUrl;
        this.elements.currentImage.style.display = 'block';
        this.elements.placeholder.style.display = 'none';

        this.elements.frameNumber.textContent = `프레임: ${this.currentFrame + 1} / ${this.images.length}`;
        this.elements.currentTime.textContent = `시간: ${(this.currentFrame / this.fps).toFixed(1)}초`;

        this.updateFrameIndicator();
    }

    updateImageCount() {
        this.elements.imageCount.textContent = `${this.images.length}개 이미지`;
    }

    updateFrameIndicator() {
        if (this.images.length === 0) return;
        
        const percentage = (this.currentFrame / (this.images.length - 1)) * 100;
        this.elements.frameIndicator.style.left = `${percentage}%`;
    }

    createTimelineScale() {
        if (this.images.length === 0) return;

        this.elements.timelineScale.innerHTML = '';
        const totalFrames = this.images.length;
        const scaleStep = Math.max(1, Math.floor(totalFrames / 10));

        for (let i = 0; i < totalFrames; i += scaleStep) {
            const mark = document.createElement('div');
            mark.className = 'scale-mark';
            mark.style.left = `${(i / (totalFrames - 1)) * 100}%`;
            
            const label = document.createElement('div');
            label.className = 'scale-label';
            label.style.left = `${(i / (totalFrames - 1)) * 100}%`;
            label.textContent = i.toString();
            
            this.elements.timelineScale.appendChild(mark);
            this.elements.timelineScale.appendChild(label);
        }
    }

    enableControls() {
        this.elements.playBtn.disabled = false;
        this.elements.prevBtn.disabled = false;
        this.elements.nextBtn.disabled = false;
        this.elements.addTagBtn.disabled = false;
        this.elements.exportBtn.disabled = false;
        this.elements.saveToServerBtn.disabled = false;
    }

    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    play() {
        if (this.images.length === 0) return;
        
        this.isPlaying = true;
        this.elements.playBtn.textContent = '⏸️ 일시정지';
        
        const interval = 1000 / (this.fps * this.playSpeed);
        this.playInterval = setInterval(() => {
            if (this.currentFrame < this.images.length - 1) {
                this.currentFrame++;
                this.updateUI();
            } else {
                this.pause();
            }
        }, interval);
    }

    pause() {
        this.isPlaying = false;
        this.elements.playBtn.textContent = '▶️ 재생';
        
        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
    }

    previousFrame() {
        if (this.currentFrame > 0) {
            this.currentFrame--;
            this.updateUI();
        }
    }

    nextFrame() {
        if (this.currentFrame < this.images.length - 1) {
            this.currentFrame++;
            this.updateUI();
        }
    }

    handleTimelineClick(e) {
        if (this.images.length === 0) return;

        const rect = this.elements.timeline.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        const newFrame = Math.floor(percentage * (this.images.length - 1));
        
        this.currentFrame = Math.max(0, Math.min(newFrame, this.images.length - 1));
        this.updateUI();
    }

    addNewTag() {
        if (this.images.length === 0) return;

        const startFrame = this.currentFrame;
        const endFrame = Math.min(startFrame + Math.floor(this.fps * 2), this.images.length - 1);

        this.editTag({
            id: Date.now(),
            name: '',
            startFrame: startFrame,
            endFrame: endFrame,
            description: ''
        }, true);
    }

    editTag(tag, isNew = false) {
        this.selectedTag = tag;
        this.elements.tagPanel.style.display = 'block';
        
        this.elements.tagName.value = tag.name;
        this.elements.tagStart.value = tag.startFrame;
        this.elements.tagEnd.value = tag.endFrame;
        this.elements.tagDescription.value = tag.description;
        
        this.elements.tagStart.max = this.images.length - 1;
        this.elements.tagEnd.max = this.images.length - 1;
        
        this.elements.deleteTagBtn.style.display = isNew ? 'none' : 'inline-flex';
        
        this.elements.tagName.focus();
    }

    saveTag() {
        if (!this.selectedTag) return;

        const name = this.elements.tagName.value.trim();
        if (!name) {
            alert('행동 이름을 입력해주세요.');
            return;
        }

        const startFrame = parseInt(this.elements.tagStart.value);
        const endFrame = parseInt(this.elements.tagEnd.value);

        if (startFrame >= endFrame) {
            alert('시작 프레임은 끝 프레임보다 작아야 합니다.');
            return;
        }

        this.selectedTag.name = name;
        this.selectedTag.startFrame = startFrame;
        this.selectedTag.endFrame = endFrame;
        this.selectedTag.description = this.elements.tagDescription.value.trim();

        if (!this.tags.find(t => t.id === this.selectedTag.id)) {
            this.tags.push(this.selectedTag);
        }

        this.updateTagsDisplay();
        this.updateTagsList();
        this.cancelTagEdit();
    }

    deleteTag() {
        if (!this.selectedTag) return;

        if (confirm('이 태그를 삭제하시겠습니까?')) {
            this.tags = this.tags.filter(t => t.id !== this.selectedTag.id);
            this.updateTagsDisplay();
            this.updateTagsList();
            this.cancelTagEdit();
        }
    }

    cancelTagEdit() {
        this.selectedTag = null;
        this.elements.tagPanel.style.display = 'none';
    }

    updateTagsDisplay() {
        if (this.images.length === 0) return;

        this.elements.tagsContainer.innerHTML = '';
        
        this.tags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag-segment';
            tagElement.setAttribute('data-tag-id', tag.id);
            
            const startPercent = (tag.startFrame / (this.images.length - 1)) * 100;
            const endPercent = (tag.endFrame / (this.images.length - 1)) * 100;
            
            tagElement.style.left = `${startPercent}%`;
            tagElement.style.width = `${endPercent - startPercent}%`;
            
            const label = document.createElement('div');
            label.className = 'tag-label';
            label.textContent = tag.name;
            tagElement.appendChild(label);
            
            tagElement.addEventListener('click', (e) => {
                e.stopPropagation();
                this.editTag(tag);
            });
            
            this.elements.tagsContainer.appendChild(tagElement);
        });
    }

    updateTagsList() {
        if (this.tags.length === 0) {
            this.elements.tagListContainer.innerHTML = '<p class="empty-message">아직 태그가 없습니다.</p>';
            return;
        }

        this.elements.tagListContainer.innerHTML = '';
        
        this.tags.sort((a, b) => a.startFrame - b.startFrame).forEach(tag => {
            const tagItem = document.createElement('div');
            tagItem.className = 'tag-item';
            
            const startTime = (tag.startFrame / this.fps).toFixed(1);
            const endTime = (tag.endFrame / this.fps).toFixed(1);
            
            tagItem.innerHTML = `
                <div class="tag-item-header">
                    <div class="tag-item-name">${tag.name}</div>
                    <div class="tag-item-frames">프레임 ${tag.startFrame}-${tag.endFrame} (${startTime}s-${endTime}s)</div>
                </div>
                ${tag.description ? `<div class="tag-item-description">${tag.description}</div>` : ''}
            `;
            
            tagItem.addEventListener('click', () => {
                this.currentFrame = tag.startFrame;
                this.updateUI();
            });
            
            tagItem.addEventListener('dblclick', () => {
                this.editTag(tag);
            });
            
            this.elements.tagListContainer.appendChild(tagItem);
        });
    }

    handleKeyboard(e) {
        if (this.images.length === 0) return;

        switch (e.key) {
            case ' ':
                e.preventDefault();
                this.togglePlay();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.previousFrame();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextFrame();
                break;
            case 'Escape':
                this.cancelTagEdit();
                break;
        }
    }

    exportData() {
        if (this.tags.length === 0) {
            alert('내보낼 태그가 없습니다.');
            return;
        }

        const data = {
            tags: this.tags,
            totalFrames: this.images.length,
            fps: this.fps,
            exportTime: new Date().toISOString(),
            version: '1.0',
            datasetName: this.currentDataset?.name || null,
            splitName: this.elements.datasetSplit.value || null
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `robot_action_tags_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
    }

    async importData(file) {
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!data.tags || !Array.isArray(data.tags)) {
                throw new Error('올바르지 않은 파일 형식입니다.');
            }

            this.tags = data.tags;
            if (data.fps) this.fps = data.fps;

            this.updateTagsDisplay();
            this.updateTagsList();
            
            alert(`${this.tags.length}개의 태그를 가져왔습니다.`);
        } catch (error) {
            alert('파일을 가져오는 중 오류가 발생했습니다: ' + error.message);
        }
    }
}

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', () => {
    new RobotActionTaggerWithDatasets();
}); 