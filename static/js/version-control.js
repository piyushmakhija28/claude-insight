/**
 * Widget Version Control JavaScript
 * Handles version history, diff viewing, and rollback functionality
 */

let currentWidgetId = null;
let versions = [];
let selectedVersion = null;

/**
 * Open version control modal
 */
function openVersionControl() {
    // Get current widget ID (assume it's stored globally or passed)
    currentWidgetId = window.currentWidgetId || 'widget_' + Date.now();

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('versionControlModal'));
    modal.show();

    // Load versions
    loadVersions();
}

/**
 * Load all versions for current widget
 */
function loadVersions() {
    const timeline = document.getElementById('versionTimeline');
    timeline.innerHTML = '<div class="text-center text-muted py-5"><i class="fas fa-spinner fa-spin fa-2x mb-3"></i><p>Loading versions...</p></div>';

    fetch(`/api/widgets/${currentWidgetId}/versions`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                versions = data.versions;
                renderVersionTimeline(versions);
                populateVersionSelects(versions);

                if (versions.length > 0) {
                    // Auto-select first version
                    showVersionDetails(versions[0].version);
                }
            } else {
                timeline.innerHTML = `<div class="alert alert-warning"><i class="fas fa-info-circle me-2"></i>No versions found. Save your widget to create the first version.</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading versions:', error);
            timeline.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-circle me-2"></i>Error loading versions</div>`;
        });
}

/**
 * Render version timeline
 */
function renderVersionTimeline(versions) {
    const timeline = document.getElementById('versionTimeline');

    if (!versions || versions.length === 0) {
        timeline.innerHTML = '<div class="text-center text-muted py-5"><i class="fas fa-code-branch fa-2x mb-3"></i><p>No versions yet</p></div>';
        return;
    }

    let html = '<div class="timeline">';

    versions.forEach((version, index) => {
        const isLatest = index === 0;
        const date = new Date(version.created_at);
        const formattedDate = date.toLocaleString();

        html += `
            <div class="version-item ${selectedVersion === version.version ? 'active' : ''}" onclick="showVersionDetails('${version.version}')">
                <div class="version-badge ${version.version_type}">
                    ${version.version}
                    ${isLatest ? '<span class="badge bg-success ms-2">Latest</span>' : ''}
                </div>
                <div class="version-meta">
                    <div class="version-type">
                        <i class="fas fa-tag me-1"></i>${version.version_type.toUpperCase()}
                    </div>
                    <div class="version-author">
                        <i class="fas fa-user me-1"></i>${version.created_by}
                    </div>
                    <div class="version-date">
                        <i class="fas fa-clock me-1"></i>${formattedDate}
                    </div>
                </div>
                <div class="version-message">${version.commit_message}</div>
                <div class="version-stats mt-2">
                    <span class="badge bg-success me-1">+${version.diff.added_lines}</span>
                    <span class="badge bg-danger">-${version.diff.removed_lines}</span>
                    ${version.diff.modified_components.map(c => `<span class="badge bg-info ms-1">${c}</span>`).join('')}
                </div>
            </div>
        `;
    });

    html += '</div>';
    timeline.innerHTML = html;
}

/**
 * Show version details
 */
function showVersionDetails(versionNumber) {
    selectedVersion = versionNumber;

    // Update timeline selection
    renderVersionTimeline(versions);

    const version = versions.find(v => v.version === versionNumber);
    if (!version) return;

    const detailsDiv = document.getElementById('versionDetails');
    const date = new Date(version.created_at);

    let html = `
        <div class="card border-0">
            <div class="card-header bg-light">
                <h5 class="mb-0">
                    <span class="badge bg-${version.version_type === 'major' ? 'danger' : version.version_type === 'minor' ? 'warning' : 'info'} me-2">
                        ${version.version}
                    </span>
                    ${version.commit_message}
                </h5>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    <div class="col-md-6">
                        <h6><i class="fas fa-info-circle me-2"></i>Information</h6>
                        <table class="table table-sm">
                            <tr>
                                <th width="40%">Version Type:</th>
                                <td><span class="badge bg-secondary">${version.version_type.toUpperCase()}</span></td>
                            </tr>
                            <tr>
                                <th>Created By:</th>
                                <td>${version.created_by}</td>
                            </tr>
                            <tr>
                                <th>Created At:</th>
                                <td>${date.toLocaleString()}</td>
                            </tr>
                            ${version.parent_version ? `<tr><th>Parent Version:</th><td>${version.parent_version}</td></tr>` : ''}
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6><i class="fas fa-chart-bar me-2"></i>Changes Summary</h6>
                        <table class="table table-sm">
                            <tr>
                                <th width="40%">Lines Added:</th>
                                <td><span class="badge bg-success">+${version.diff.added_lines}</span></td>
                            </tr>
                            <tr>
                                <th>Lines Removed:</th>
                                <td><span class="badge bg-danger">-${version.diff.removed_lines}</span></td>
                            </tr>
                            <tr>
                                <th>Modified:</th>
                                <td>${version.diff.modified_components.join(', ') || 'None'}</td>
                            </tr>
                        </table>
                    </div>
                </div>

                <hr>

                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-primary" onclick="viewVersionSnapshot('${version.version}')">
                        <i class="fas fa-eye me-1"></i>View Snapshot
                    </button>
                    ${version.parent_version ? `
                        <button class="btn btn-sm btn-info" onclick="quickDiff('${version.parent_version}', '${version.version}')">
                            <i class="fas fa-code-compare me-1"></i>Compare with Parent
                        </button>
                    ` : ''}
                    ${versions[0].version !== version.version ? `
                        <button class="btn btn-sm btn-warning" onclick="confirmRollback('${version.version}')">
                            <i class="fas fa-undo me-1"></i>Rollback to This Version
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

    detailsDiv.innerHTML = html;
}

/**
 * Populate version select dropdowns
 */
function populateVersionSelects(versions) {
    const fromSelect = document.getElementById('diffFromVersion');
    const toSelect = document.getElementById('diffToVersion');

    let options = '<option value="">Select version...</option>';
    versions.forEach(v => {
        options += `<option value="${v.version}">${v.version} - ${v.commit_message}</option>`;
    });

    fromSelect.innerHTML = options;
    toSelect.innerHTML = options;

    // Pre-select last two versions if available
    if (versions.length >= 2) {
        fromSelect.value = versions[1].version;
        toSelect.value = versions[0].version;
    }
}

/**
 * Compare versions (diff viewer)
 */
function compareDiff() {
    const fromVersion = document.getElementById('diffFromVersion').value;
    const toVersion = document.getElementById('diffToVersion').value;

    if (!fromVersion || !toVersion) {
        alert('Please select both versions to compare');
        return;
    }

    quickDiff(fromVersion, toVersion);
}

/**
 * Quick diff between two versions
 */
function quickDiff(fromVersion, toVersion) {
    const diffViewer = document.getElementById('diffViewer');
    diffViewer.innerHTML = '<div class="text-center py-5"><i class="fas fa-spinner fa-spin fa-2x"></i></div>';

    // Switch to diff tab
    const diffTab = new bootstrap.Tab(document.querySelector('a[href="#versionDiffTab"]'));
    diffTab.show();

    // Update select boxes
    document.getElementById('diffFromVersion').value = fromVersion;
    document.getElementById('diffToVersion').value = toVersion;

    fetch(`/api/widgets/${currentWidgetId}/versions/${toVersion}/diff?from=${fromVersion}&to=${toVersion}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderDiff(data.diff);
            } else {
                diffViewer.innerHTML = `<div class="alert alert-danger">Error loading diff</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading diff:', error);
            diffViewer.innerHTML = `<div class="alert alert-danger">Error loading diff</div>`;
        });
}

/**
 * Render diff viewer
 */
function renderDiff(diffData) {
    const diffViewer = document.getElementById('diffViewer');

    let html = `
        <div class="diff-summary mb-3">
            <h6>Changes: ${diffData.from_version} → ${diffData.to_version}</h6>
            <div class="d-flex gap-3">
                <span><span class="badge bg-success">+${diffData.summary.added_lines}</span> lines added</span>
                <span><span class="badge bg-danger">-${diffData.summary.removed_lines}</span> lines removed</span>
            </div>
        </div>
    `;

    // Render diffs for each component
    if (diffData.diffs.html) {
        html += renderComponentDiff('HTML', diffData.diffs.html);
    }

    if (diffData.diffs.css) {
        html += renderComponentDiff('CSS', diffData.diffs.css);
    }

    if (diffData.diffs.javascript) {
        html += renderComponentDiff('JavaScript', diffData.diffs.javascript);
    }

    if (!diffData.diffs.html && !diffData.diffs.css && !diffData.diffs.javascript) {
        html += '<div class="alert alert-info"><i class="fas fa-info-circle me-2"></i>No differences found</div>';
    }

    diffViewer.innerHTML = html;
}

/**
 * Render component diff (HTML, CSS, or JS)
 */
function renderComponentDiff(componentName, diffLines) {
    let html = `
        <div class="diff-section mb-3">
            <h6 class="diff-header">
                <i class="fas fa-code me-2"></i>${componentName}
            </h6>
            <div class="diff-content">
                <pre class="diff-pre">`;

    diffLines.forEach(line => {
        let cssClass = '';
        let icon = '';

        if (line.startsWith('+++') || line.startsWith('---')) {
            cssClass = 'diff-file-header';
        } else if (line.startsWith('+')) {
            cssClass = 'diff-added';
            icon = '+ ';
        } else if (line.startsWith('-')) {
            cssClass = 'diff-removed';
            icon = '- ';
        } else if (line.startsWith('@@')) {
            cssClass = 'diff-hunk-header';
        } else {
            cssClass = 'diff-context';
            icon = '  ';
        }

        html += `<div class="${cssClass}">${escapeHtml(line)}</div>`;
    });

    html += `</pre></div></div>`;
    return html;
}

/**
 * View version snapshot
 */
function viewVersionSnapshot(versionNumber) {
    fetch(`/api/widgets/${currentWidgetId}/versions/${versionNumber}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show in a new modal or overlay
                showSnapshotPreview(versionNumber, data.version_data);
            } else {
                alert('Error loading snapshot');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error loading snapshot');
        });
}

/**
 * Show snapshot preview
 */
function showSnapshotPreview(version, snapshotData) {
    // Create a simple preview
    const preview = `
        <div class="modal fade" id="snapshotPreviewModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Snapshot: Version ${version}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <pre class="bg-light p-3" style="max-height: 500px; overflow-y: auto;">${escapeHtml(JSON.stringify(snapshotData, null, 2))}</pre>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if any
    const existing = document.getElementById('snapshotPreviewModal');
    if (existing) existing.remove();

    // Add and show new modal
    document.body.insertAdjacentHTML('beforeend', preview);
    const modal = new bootstrap.Modal(document.getElementById('snapshotPreviewModal'));
    modal.show();

    // Clean up on hide
    document.getElementById('snapshotPreviewModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

/**
 * Create new version
 */
function createNewVersion() {
    // Get current version
    const currentVersion = versions.length > 0 ? versions[0].version : '0.0.0';
    document.getElementById('currentVersionDisplay').textContent = currentVersion;

    // Calculate new version based on type
    updateNewVersionDisplay();

    // Show create version modal
    const modal = new bootstrap.Modal(document.getElementById('createVersionModal'));
    modal.show();

    // Add event listener for version type change
    document.getElementById('versionType').addEventListener('change', updateNewVersionDisplay);
}

/**
 * Update new version display
 */
function updateNewVersionDisplay() {
    const currentVersion = document.getElementById('currentVersionDisplay').textContent;
    const versionType = document.getElementById('versionType').value;

    const [major, minor, patch] = currentVersion.split('.').map(Number);

    let newVersion;
    if (versionType === 'major') {
        newVersion = `${major + 1}.0.0`;
    } else if (versionType === 'minor') {
        newVersion = `${major}.${minor + 1}.0`;
    } else {
        newVersion = `${major}.${minor}.${patch + 1}`;
    }

    document.getElementById('newVersionDisplay').textContent = newVersion;
}

/**
 * Save new version
 */
function saveNewVersion() {
    const versionType = document.getElementById('versionType').value;
    const commitMessage = document.getElementById('commitMessage').value.trim();

    if (!commitMessage) {
        alert('Please enter a commit message');
        return;
    }

    // Get current widget data (you'll need to implement this based on your widget structure)
    const widgetData = getCurrentWidgetData();

    fetch(`/api/widgets/${currentWidgetId}/versions/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            widget_data: widgetData,
            version_type: versionType,
            commit_message: commitMessage
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Close create modal
            bootstrap.Modal.getInstance(document.getElementById('createVersionModal')).hide();

            // Reload versions
            loadVersions();

            // Show success message
            showToast('Success', 'New version created successfully', 'success');
        } else {
            alert('Error creating version: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error creating version');
    });
}

/**
 * Get current widget data
 */
function getCurrentWidgetData() {
    // This should gather the current widget state
    // Adjust based on your actual widget structure
    return {
        name: document.getElementById('widgetName')?.value || 'Untitled Widget',
        description: document.getElementById('widgetDescription')?.value || '',
        html_content: document.getElementById('widgetCanvas')?.innerHTML || '',
        css_content: document.getElementById('widgetCss')?.value || '',
        js_content: document.getElementById('widgetJs')?.value || '',
        components: window.widgetData?.components || []
    };
}

/**
 * Confirm rollback
 */
function confirmRollback(targetVersion) {
    if (confirm(`Are you sure you want to rollback to version ${targetVersion}? This will create a new version with the old content.`)) {
        rollbackToVersion(targetVersion);
    }
}

/**
 * Rollback to version
 */
function rollbackToVersion(targetVersion) {
    fetch(`/api/widgets/${currentWidgetId}/versions/${targetVersion}/rollback`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Success', 'Rolled back to version ' + targetVersion, 'success');
            loadVersions();

            // Reload widget data (you'll need to implement this)
            // reloadWidgetData(data.new_version);
        } else {
            alert('Error during rollback: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error during rollback');
    });
}

/**
 * Utility: Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Utility: Show toast notification
 */
function showToast(title, message, type = 'info') {
    // Simple toast implementation - you can use Bootstrap Toast or a library
    alert(`${title}: ${message}`);
}
