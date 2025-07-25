class LiberoActionTagger {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8001/api/libero';
        this.currentEpisode = null;
        this.currentFrameIndex = 0;
        this.isPlaying = false;
        this.playInterval = null;
        this.playSpeed = 1;
        this.tags = [];
        this.selectedTag = null;
        this.fps = 10;
        this.sessionId = this.generateSessionId();
        this.liberoInfo = null;
        this.episodes = [];
        this.tasks = [];
        this.tagTemplates = this.loadTagTemplates();

        this.initializeElements();
        this.bindEvents();
        this.loadLiberoInfo();
    }

    generateSessionId() {
        return `libero_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
    }

    initializeElements() {
        this.elements = {
            // 상태 및 통계
            datasetStatus: document.getElementById('datasetStatus'),
            liberoStats: document.getElementById('liberoStats'),
            totalFrames: document.getElementById('totalFrames'),
            totalEpisodes: document.getElementById('totalEpisodes'),
            totalTasks: document.getElementById('totalTasks'),

            // 에피소드 브라우저
            taskFilter: document.getElementById('taskFilter'),
            loadEpisodesBtn: document.getElementById('loadEpisodesBtn'),
            episodeGrid: document.getElementById('episodeGrid'),

            // 듀얼 카메라
            mainCamera: document.getElementById('mainCamera'),
            wristCamera: document.getElementById('wristCamera'),
            mainPlaceholder: document.getElementById('mainPlaceholder'),
            wristPlaceholder: document.getElementById('wristPlaceholder'),

            // 프레임 정보
            frameNumber: document.getElementById('frameNumber'),
            currentTime: document.getElementById('currentTime'),
            episodeInfo: document.getElementById('episodeInfo'),

            // 로봇 데이터
            robotState: document.getElementById('robotState'),
            robotActions: document.getElementById('robotActions'),

            // 컨트롤
            playBtn: document.getElementById('playBtn'),
            prevBtn: document.getElementById('prevBtn'),
            nextBtn: document.getElementById('nextBtn'),
            frameInput: document.getElementById('frameInput'),
            goToFrameBtn: document.getElementById('goToFrameBtn'),
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
            tagTemplatesSection: document.getElementById('tagTemplatesSection'),
            tagTemplates: document.getElementById('tagTemplates'),
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
        // 에피소드 브라우저
        this.elements.loadEpisodesBtn.addEventListener('click', () => {
            this.loadEpisodes();
        });

        this.elements.taskFilter.addEventListener('change', () => {
            this.loadEpisodes();
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

        this.elements.goToFrameBtn.addEventListener('click', () => {
            this.goToFrame();
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

    async loadLiberoInfo() {
        try {
            this.elements.datasetStatus.textContent = 'Libero 데이터셋 로딩 중...';
            
            const response = await fetch(`${this.apiBaseUrl}/info`);
            if (!response.ok) {
                throw new Error(`데이터셋 정보 로드 실패: ${response.status}`);
            }

            this.liberoInfo = await response.json();
            
            // 통계 업데이트
            this.elements.totalFrames.textContent = this.liberoInfo.total_frames.toLocaleString();
            this.elements.totalEpisodes.textContent = this.liberoInfo.total_episodes.toLocaleString();
            this.elements.totalTasks.textContent = this.liberoInfo.total_tasks;
            
            this.elements.liberoStats.style.display = 'grid';
            this.elements.datasetStatus.textContent = `✅ Libero 데이터셋 연결됨 (${this.liberoInfo.total_frames.toLocaleString()}개 프레임)`;

            // 태스크 목록 로드
            await this.loadTasks();

        } catch (error) {
            this.elements.datasetStatus.textContent = `❌ 연결 실패: ${error.message}`;
            this.showError(`Libero 데이터셋 로드 실패: ${error.message}`);
        }
    }

    async loadTasks() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tasks`);
            if (!response.ok) {
                throw new Error(`태스크 로드 실패: ${response.status}`);
            }

            this.tasks = await response.json();
            
            // 태스크 필터 옵션 업데이트
            this.elements.taskFilter.innerHTML = '<option value="">모든 태스크</option>';
            this.tasks.forEach(task => {
                const option = document.createElement('option');
                option.value = task.task_index;
                option.textContent = `태스크 ${task.task_index} (${task.episode_count}개 에피소드)`;
                this.elements.taskFilter.appendChild(option);
            });

            // 자동으로 에피소드 로드
            await this.loadEpisodes();

        } catch (error) {
            console.error('태스크 로드 실패:', error);
        }
    }

    async loadEpisodes() {
        try {
            this.elements.episodeGrid.innerHTML = '<div class="loading-indicator">에피소드를 로딩 중...</div>';
            
            const taskIndex = this.elements.taskFilter.value;
            const params = new URLSearchParams();
            if (taskIndex) params.append('task_index', taskIndex);
            params.append('limit', '50');

            const response = await fetch(`${this.apiBaseUrl}/episodes?${params}`);
            if (!response.ok) {
                throw new Error(`에피소드 로드 실패: ${response.status}`);
            }

            this.episodes = await response.json();
            this.displayEpisodes();

        } catch (error) {
            this.elements.episodeGrid.innerHTML = `<div class="error-message">에피소드 로드 실패: ${error.message}</div>`;
        }
    }

    async displayEpisodes() {
        this.elements.episodeGrid.innerHTML = '';

        for (const episode of this.episodes) {
            const episodeCard = document.createElement('div');
            episodeCard.className = 'episode-card';
            episodeCard.innerHTML = `
                <div class="episode-thumbnail">
                    <div style="color: #666; font-size: 12px;">로딩 중...</div>
                </div>
                <div class="episode-info">
                    <div class="episode-number">에피소드 ${episode.episode_index}</div>
                    <div class="episode-task">태스크 ${episode.task_index}</div>
                    <div class="episode-stats">${episode.frame_count}프레임</div>
                </div>
            `;

            episodeCard.addEventListener('click', () => {
                this.selectEpisode(episode.episode_index);
            });

            this.elements.episodeGrid.appendChild(episodeCard);

            // 비동기로 썸네일 로드
            this.loadEpisodeThumbnail(episode.episode_index, episodeCard);
        }
    }

    async loadEpisodeThumbnail(episodeIndex, episodeCard) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/episode/${episodeIndex}/thumbnail`);
            if (!response.ok) return;

            const data = await response.json();
            const thumbnail = episodeCard.querySelector('.episode-thumbnail');
            thumbnail.innerHTML = `<img src="data:image/png;base64,${data.thumbnail}" alt="에피소드 ${episodeIndex}">`;

        } catch (error) {
            // 썸네일 로드 실패는 무시
        }
    }

    async selectEpisode(episodeIndex) {
        try {
            // 이전 선택 해제
            document.querySelectorAll('.episode-card').forEach(card => {
                card.classList.remove('selected');
            });

            // 현재 선택 표시
            const selectedCard = Array.from(document.querySelectorAll('.episode-card')).find(card => {
                const episodeNum = card.querySelector('.episode-number').textContent.match(/\d+/)[0];
                return parseInt(episodeNum) === episodeIndex;
            });
            if (selectedCard) {
                selectedCard.classList.add('selected');
            }

            // 에피소드 데이터 로드
            this.showLoading();
            
            // 에피소드 목록에서 실제 frame_count 찾기
            const selectedEpisode = this.episodes.find(ep => ep.episode_index === episodeIndex);
            const maxFrames = selectedEpisode ? selectedEpisode.frame_count : 500;
            
            const response = await fetch(`${this.apiBaseUrl}/episode/${episodeIndex}?frame_count=${maxFrames}`);
            if (!response.ok) {
                throw new Error(`에피소드 로드 실패: ${response.status}`);
            }

            this.currentEpisode = await response.json();
            this.currentFrameIndex = 0;
            
            this.updateUI();
            this.createTimelineScale();
            this.enableControls();

        } catch (error) {
            this.showError(`에피소드 선택 실패: ${error.message}`);
        }
    }

    showLoading() {
        this.elements.mainPlaceholder.textContent = '에피소드 로딩 중...';
        this.elements.wristPlaceholder.textContent = '에피소드 로딩 중...';
    }

    updateUI() {
        if (!this.currentEpisode || this.currentEpisode.frames.length === 0) return;

        const currentFrame = this.currentEpisode.frames[this.currentFrameIndex];
        
        // 듀얼 카메라 업데이트
        this.elements.mainCamera.src = `data:image/png;base64,${currentFrame.image}`;
        this.elements.mainCamera.style.display = 'block';
        this.elements.mainPlaceholder.style.display = 'none';

        this.elements.wristCamera.src = `data:image/png;base64,${currentFrame.wrist_image}`;
        this.elements.wristCamera.style.display = 'block';
        this.elements.wristPlaceholder.style.display = 'none';

        // 프레임 정보 업데이트 (전체 에피소드 길이 표시)
        const totalFramesInEpisode = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
        this.elements.frameNumber.textContent = `프레임: ${this.currentFrameIndex + 1} / ${totalFramesInEpisode}`;
        this.elements.currentTime.textContent = `시간: ${currentFrame.timestamp.toFixed(2)}초`;
        this.elements.episodeInfo.textContent = `에피소드: ${currentFrame.episode_index}, 태스크: ${currentFrame.task_index}`;

        // 로봇 데이터 업데이트
        this.updateRobotData(currentFrame);

        // 타임라인 인디케이터 업데이트
        this.updateFrameIndicator();

        // 프레임 입력 업데이트
        this.elements.frameInput.value = this.currentFrameIndex;
    }

    updateRobotData(frame) {
        // 로봇 상태 업데이트
        const stateElements = this.elements.robotState.querySelectorAll('.data-value');
        frame.state.forEach((value, index) => {
            if (stateElements[index]) {
                stateElements[index].textContent = value.toFixed(3);
            }
        });

        // 로봇 액션 업데이트
        const actionElements = this.elements.robotActions.querySelectorAll('.data-value');
        frame.actions.forEach((value, index) => {
            if (actionElements[index]) {
                actionElements[index].textContent = value.toFixed(3);
            }
        });
    }

    updateFrameIndicator() {
        if (!this.currentEpisode || this.currentEpisode.frames.length === 0) return;
        
        // 전체 에피소드 길이를 기준으로 인디케이터 위치 계산
        const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
        const percentage = (this.currentFrameIndex / (totalFrames - 1)) * 100;
        this.elements.frameIndicator.style.left = `${percentage}%`;
    }

    createTimelineScale() {
        if (!this.currentEpisode) return;

        this.elements.timelineScale.innerHTML = '';
        // 전체 에피소드 길이를 기준으로 스케일 생성
        const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
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
        this.elements.frameInput.disabled = false;
        // 전체 에피소드 길이를 기준으로 max 설정
        const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
        this.elements.frameInput.max = totalFrames - 1;
        this.elements.goToFrameBtn.disabled = false;
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
        if (!this.currentEpisode) return;
        
        this.isPlaying = true;
        this.elements.playBtn.textContent = '⏸️ 일시정지';
        
        const interval = 1000 / (this.fps * this.playSpeed);
        this.playInterval = setInterval(() => {
            // 전체 에피소드 길이를 기준으로 재생
            const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
            const maxLoadedFrame = this.currentEpisode.frames.length - 1;
            
            if (this.currentFrameIndex < Math.min(totalFrames - 1, maxLoadedFrame)) {
                this.currentFrameIndex++;
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
        if (this.currentFrameIndex > 0) {
            this.currentFrameIndex--;
            this.updateUI();
        }
    }

    nextFrame() {
        if (this.currentEpisode) {
            // 전체 에피소드 길이를 기준으로 다음 프레임 이동
            const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
            const maxLoadedFrame = this.currentEpisode.frames.length - 1;
            
            if (this.currentFrameIndex < Math.min(totalFrames - 1, maxLoadedFrame)) {
                this.currentFrameIndex++;
                this.updateUI();
            }
        }
    }

    goToFrame() {
        const frameNum = parseInt(this.elements.frameInput.value);
        if (this.currentEpisode && frameNum >= 0) {
            // 전체 에피소드 길이를 기준으로 프레임 이동
            const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
            const maxLoadedFrame = this.currentEpisode.frames.length - 1;
            
            if (frameNum < totalFrames && frameNum <= maxLoadedFrame) {
                this.currentFrameIndex = frameNum;
                this.updateUI();
            } else if (frameNum >= totalFrames) {
                alert(`프레임 번호는 0부터 ${totalFrames - 1}까지 입력 가능합니다.`);
            } else if (frameNum > maxLoadedFrame) {
                alert(`현재 ${maxLoadedFrame + 1}개 프레임만 로드되었습니다. 프레임 ${frameNum}은 아직 로드되지 않았습니다.`);
            }
        }
    }

    handleTimelineClick(e) {
        if (!this.currentEpisode) return;

        const rect = this.elements.timeline.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        
        // 전체 에피소드 길이를 기준으로 프레임 계산
        const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
        const newFrame = Math.floor(percentage * (totalFrames - 1));
        
        // 현재 로드된 프레임 범위 내에서만 이동 가능
        this.currentFrameIndex = Math.max(0, Math.min(newFrame, this.currentEpisode.frames.length - 1));
        this.updateUI();
    }

    addNewTag() {
        if (!this.currentEpisode) return;

        const startFrame = this.currentFrameIndex;
        // 전체 에피소드 길이를 기준으로 태그 범위 설정
        const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
        const endFrame = Math.min(startFrame + Math.floor(this.fps * 2), totalFrames - 1);

        this.editTag({
            id: Date.now(),
            name: '',
            startFrame: startFrame,
            endFrame: endFrame,
            description: ''
        }, true);
    }

    // 태그 템플릿 관리 메서드들
    loadTagTemplates() {
        try {
            const stored = localStorage.getItem('libero_tag_templates');
            return stored ? JSON.parse(stored) : {};
        } catch (error) {
            console.error('태그 템플릿 로드 실패:', error);
            return {};
        }
    }

    saveTagTemplates() {
        try {
            localStorage.setItem('libero_tag_templates', JSON.stringify(this.tagTemplates));
        } catch (error) {
            console.error('태그 템플릿 저장 실패:', error);
        }
    }

    addTagTemplate(name, description = '') {
        if (!name.trim()) return;
        
        const key = name.trim();
        if (!this.tagTemplates[key]) {
            this.tagTemplates[key] = {
                name: key,
                description: description,
                usageCount: 0,
                lastUsed: new Date().toISOString()
            };
        }
        
        this.tagTemplates[key].usageCount++;
        this.tagTemplates[key].lastUsed = new Date().toISOString();
        this.saveTagTemplates();
        this.displayTagTemplates();
    }

    displayTagTemplates() {
        const container = this.elements.tagTemplates;
        
        // 템플릿이 없는 경우
        const templateKeys = Object.keys(this.tagTemplates);
        if (templateKeys.length === 0) {
            container.innerHTML = '<p class="empty-templates">저장된 태그가 없습니다.</p>';
            return;
        }

        // 사용 횟수 순으로 정렬
        const sortedTemplates = templateKeys
            .map(key => this.tagTemplates[key])
            .sort((a, b) => b.usageCount - a.usageCount);

        container.innerHTML = '';
        
        sortedTemplates.forEach(template => {
            const templateElement = document.createElement('div');
            templateElement.className = 'tag-template-item';
            templateElement.innerHTML = `
                <span class="template-name">${template.name}</span>
                <span class="usage-count">${template.usageCount}</span>
            `;
            
            templateElement.addEventListener('click', () => {
                this.applyTagTemplate(template);
            });
            
            container.appendChild(templateElement);
        });
    }

    applyTagTemplate(template) {
        if (!this.currentEpisode) return;

        const startFrame = this.currentFrameIndex;
        const endFrame = Math.min(startFrame + Math.floor(this.fps * 2), this.currentEpisode.frames.length - 1);

        // 템플릿을 현재 프레임에 적용
        this.elements.tagName.value = template.name;
        this.elements.tagStart.value = startFrame;
        this.elements.tagEnd.value = endFrame;
        this.elements.tagDescription.value = template.description || '';

        // 사용 횟수 증가
        this.addTagTemplate(template.name, template.description);
    }

    editTag(tag, isNew = false) {
        this.selectedTag = tag;
        this.elements.tagPanel.style.display = 'block';
        
        this.elements.tagName.value = tag.name;
        this.elements.tagStart.value = tag.startFrame;
        this.elements.tagEnd.value = tag.endFrame;
        this.elements.tagDescription.value = tag.description;
        
        if (this.currentEpisode) {
            // 전체 에피소드 길이를 기준으로 태그 편집 범위 설정
            const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
            this.elements.tagStart.max = totalFrames - 1;
            this.elements.tagEnd.max = totalFrames - 1;
        }
        
        this.elements.deleteTagBtn.style.display = isNew ? 'none' : 'inline-flex';
        
        // 태그 템플릿 표시
        this.displayTagTemplates();
        
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

        // 태그 템플릿에 추가
        this.addTagTemplate(name, this.selectedTag.description);

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
        if (!this.currentEpisode) return;

        this.elements.tagsContainer.innerHTML = '';
        
        // 전체 에피소드 길이를 기준으로 태그 위치 계산
        const totalFrames = this.currentEpisode.metadata?.total_frames_in_episode || this.currentEpisode.frames.length;
        
        this.tags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'tag-segment';
            tagElement.setAttribute('data-tag-id', tag.id);
            
            const startPercent = (tag.startFrame / (totalFrames - 1)) * 100;
            const endPercent = (tag.endFrame / (totalFrames - 1)) * 100;
            
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
                this.currentFrameIndex = tag.startFrame;
                this.updateUI();
            });
            
            tagItem.addEventListener('dblclick', () => {
                this.editTag(tag);
            });
            
            this.elements.tagListContainer.appendChild(tagItem);
        });
    }

    handleKeyboard(e) {
        if (!this.currentEpisode) return;

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

    async saveToServer() {
        try {
            const data = {
                tags: this.tags,
                totalFrames: this.currentEpisode ? this.currentEpisode.frames.length : 0,
                fps: this.fps,
                exportTime: new Date().toISOString(),
                version: '1.0',
                episodeIndex: this.currentEpisode ? this.currentEpisode.episode_index : null,
                taskIndex: this.currentEpisode ? this.currentEpisode.task_index : null
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

            alert(`서버에 저장되었습니다.\n세션 ID: ${this.sessionId}`);

        } catch (error) {
            alert(`서버 저장 중 오류 발생: ${error.message}`);
        }
    }

    exportData() {
        if (this.tags.length === 0) {
            alert('내보낼 태그가 없습니다.');
            return;
        }

        const data = {
            tags: this.tags,
            totalFrames: this.currentEpisode ? this.currentEpisode.frames.length : 0,
            fps: this.fps,
            exportTime: new Date().toISOString(),
            version: '1.0',
            episodeIndex: this.currentEpisode ? this.currentEpisode.episode_index : null,
            taskIndex: this.currentEpisode ? this.currentEpisode.task_index : null,
            datasetName: 'physical-intelligence/libero'
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        const filename = `libero_episode_${this.currentEpisode?.episode_index || 'unknown'}_tags_${new Date().toISOString().split('T')[0]}.json`;
        a.download = filename;
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
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // 첫 번째 main 요소에 추가
        const main = document.querySelector('main');
        if (main) {
            main.insertBefore(errorDiv, main.firstChild);
            
            // 5초 후 자동 제거
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.parentNode.removeChild(errorDiv);
                }
            }, 5000);
        }
    }
}

// 애플리케이션 시작
document.addEventListener('DOMContentLoaded', () => {
    new LiberoActionTagger();
}); 