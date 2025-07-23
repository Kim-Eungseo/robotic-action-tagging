class RobotActionTagger {
    constructor() {
        this.images = [];
        this.currentFrame = 0;
        this.isPlaying = false;
        this.playInterval = null;
        this.playSpeed = 1;
        this.tags = [];
        this.selectedTag = null;
        this.fps = 10; // 기본 프레임 레이트

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // DOM 요소들
        this.elements = {
            // 업로드 관련
            imageUpload: document.getElementById('imageUpload'),
            uploadBtn: document.getElementById('uploadBtn'),
            imageCount: document.getElementById('imageCount'),
            
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
            importInput: document.getElementById('importInput')
        };
    }

    bindEvents() {
        // 업로드 이벤트
        this.elements.uploadBtn.addEventListener('click', () => {
            this.elements.imageUpload.click();
        });

        this.elements.imageUpload.addEventListener('change', (e) => {
            this.handleImageUpload(e.target.files);
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

        // 키보드 이벤트
        document.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
    }

    async handleImageUpload(files) {
        if (files.length === 0) return;

        // 파일을 배열로 변환하고 이름으로 정렬
        const fileArray = Array.from(files).sort((a, b) => a.name.localeCompare(b.name));
        
        this.images = [];
        this.elements.imageCount.textContent = `${fileArray.length}개 이미지 로딩 중...`;

        // 이미지들을 Data URL로 변환
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

        // 현재 이미지 표시
        this.elements.currentImage.src = this.images[this.currentFrame].dataUrl;
        this.elements.currentImage.style.display = 'block';
        this.elements.placeholder.style.display = 'none';

        // 프레임 정보 업데이트
        this.elements.frameNumber.textContent = `프레임: ${this.currentFrame + 1} / ${this.images.length}`;
        this.elements.currentTime.textContent = `시간: ${(this.currentFrame / this.fps).toFixed(1)}초`;

        // 타임라인 인디케이터 위치 업데이트
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
        const endFrame = Math.min(startFrame + Math.floor(this.fps * 2), this.images.length - 1); // 2초 기본 길이

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

        // 새 태그인 경우 추가
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
            version: '1.0'
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

    showError(message) {
        const errorContainer = document.getElementById('error-container');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // 기존 에러 메시지 제거
        while (errorContainer.firstChild) {
            errorContainer.removeChild(errorContainer.firstChild);
        }
        
        errorContainer.appendChild(errorDiv);
        
        // 5초 후 자동으로 사라짐
        setTimeout(() => {
            if (errorDiv.parentNode === errorContainer) {
                errorDiv.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    if (errorDiv.parentNode === errorContainer) {
                        errorContainer.removeChild(errorDiv);
                    }
                }, 300);
            }
        }, 5000);
    }
}

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', () => {
    new RobotActionTagger();
}); 

// 애니메이션 스타일 추가
const style = document.createElement('style');
style.textContent = `
@keyframes fadeOut {
    from {
        opacity: 1;
        transform: translate(-50%, 0);
    }
    to {
        opacity: 0;
        transform: translate(-50%, -100%);
    }
}`;
document.head.appendChild(style); 