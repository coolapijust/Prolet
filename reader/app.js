(function() {
  const viewer = document.getElementById('viewer');
  const sidebarList = document.getElementById('sidebar-list');
  const sidebarTitle = document.getElementById('sidebar-title');
  const backToTop = document.getElementById('back-to-top');
  const searchContainer = document.getElementById('search-container');
  const searchInput = document.getElementById('search-input');
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebar-toggle');
  const themeToggle = document.getElementById('theme-toggle');
  const sidebarToggleCollapsed = document.getElementById('sidebar-toggle-collapsed');
  const themeToggleCollapsed = document.getElementById('theme-toggle-collapsed');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const sidebarOverlay = document.getElementById('sidebar-overlay');
  
  let allDocs = [];
  let searchTimeout = null;
  let config = null;

  function loadConfig() {
    return fetch('config.json?t=' + Date.now())
      .then(r => r.json())
      .then(cfg => {
        config = cfg;
        console.log('[Config] 加载配置:', JSON.stringify(config));
        if (config.site_title) {
          document.title = config.site_title;
        }
        if (config.sidebar_title) {
          sidebarTitle.textContent = config.sidebar_title;
        }
        if (config.max_content_width) {
          document.querySelector('.content').style.maxWidth = config.max_content_width + 'px';
        }
        if (config.enable_back_to_top === false) {
          backToTop.style.display = 'none';
        }
        if (config.enable_search === true) {
          searchContainer.style.display = 'block';
        }
        return config;
      })
      .catch(() => {
        console.log('[App] 使用默认配置');
        searchContainer.style.display = 'block';
        return {};
      });
  }

  function countFiles(items) {
    let count = 0;
    for (const item of items) {
      if (item.type === 'file') {
        count++;
      } else if (item.type === 'folder' && item.children) {
        count += countFiles(item.children);
      }
    }
    return count;
  }

  function flattenDocs(items, result = []) {
    for (const item of items) {
      if (item.type === 'file') {
        result.push(item);
      } else if (item.type === 'folder' && item.children) {
        flattenDocs(item.children, result);
      }
    }
    return result;
  }

  function loadSidebar() {
    fetch('index.json')
      .then(r => {
        if (!r.ok) throw new Error('索引文件不存在');
        return r.json();
      })
      .then(data => {
        allDocs = flattenDocs(data);
        renderSidebar(data);
      })
      .catch(err => {
        console.log('[App] ' + err.message);
        sidebarList.innerHTML = '<li>请在config.json中配置source_dir</li>';
      });
  }

  function renderSidebar(data, isRoot = true) {
    let html = '';
    data.forEach((item) => {
      html += renderSidebarItem(item, 0, 0);
    });
    sidebarList.innerHTML = html || '<li>暂无文档</li>';
    attachFolderListeners();
  }

  function renderSidebarItem(item, index = 0, depth = 0) {
    if (item.type === 'folder') {
      const totalFiles = countFiles(item.children || []);
      const isCollapsed = totalFiles >= 4;
      const folderId = `folder-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const state = isCollapsed ? 'collapsed' : 'expanded';
      const arrow = isCollapsed ? '▶' : '▼';
      let html = `<li class="folder" data-folder-id="${folderId}" data-state="${state}">
        <span class="folder-name">${escapeHtml(item.name)}<span class="folder-arrow">${arrow}</span></span>
      </li>`;
      if (item.children && item.children.length > 0) {
        html += `<ul class="folder-children" data-parent="${folderId}" style="display:${isCollapsed ? 'none' : 'block'}">`;
        item.children.forEach((child) => {
          html += renderSidebarItem(child, 0, depth + 1);
        });
        html += '</ul>';
      }
      return html;
    }
    const indent = depth > 0 ? `style="padding-left: ${depth * 20}px"` : '';
    const safePath = encodeURIComponent(item.path);
    const safeTitle = escapeHtml(item.title);
    return `<li class="sub-item" ${indent}><a onclick="window.loadDoc('${safePath}')">${safeTitle}</a></li>`;
  }

  function attachFolderListeners() {
    document.querySelectorAll('.folder').forEach(folder => {
      folder.addEventListener('click', (e) => {
        if (e.target.closest('.sub-item')) return;
        const folderId = folder.dataset.folderId;
        const children = document.querySelector(`.folder-children[data-parent="${folderId}"]`);
        if (children) {
          const isCollapsed = children.style.display === 'none';
          children.style.display = isCollapsed ? 'block' : 'none';
          folder.dataset.state = isCollapsed ? 'expanded' : 'collapsed';
          folder.querySelector('.folder-arrow').textContent = isCollapsed ? '▼' : '▶';
        }
      });
    });
  }

  function renderSearchResults(results) {
    if (results.length === 0) {
      sidebarList.innerHTML = '<li>未找到匹配的文档</li>';
      return;
    }
    let html = '<li class="folder">搜索结果</li>';
    results.forEach(item => {
      html += `<li class="sub-item"><a onclick="window.loadDoc('${item.path}')">${item.title}</a></li>`;
    });
    sidebarList.innerHTML = html;
  }

  function handleSearch(query) {
    if (!query.trim()) {
      fetch('index.json')
        .then(r => r.json())
        .then(data => renderSidebar(data));
      return;
    }
    
    const lowerQuery = query.toLowerCase();
    const results = allDocs.filter(doc => 
      doc.title.toLowerCase().includes(lowerQuery) ||
      doc.name.toLowerCase().includes(lowerQuery) ||
      doc.path.toLowerCase().includes(lowerQuery)
    );
    renderSearchResults(results);
  }

  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      handleSearch(e.target.value);
    }, 200);
  });

  sidebarToggle.addEventListener('click', () => {
    const isCollapsed = sidebar.classList.toggle('collapsed');
    sidebarToggle.querySelector('svg path').setAttribute('d', isCollapsed ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6');
    sidebarToggle.title = isCollapsed ? '展开侧边栏' : '收起侧边栏';
    localStorage.setItem('sidebarCollapsed', isCollapsed);
  });

  themeToggle.addEventListener('click', () => {
    toggleTheme();
  });

  sidebarToggleCollapsed.addEventListener('click', () => {
    sidebar.classList.remove('collapsed');
    sidebarToggle.querySelector('svg path').setAttribute('d', 'M15 18l-6-6 6-6');
    sidebarToggle.title = '收起侧边栏';
    localStorage.setItem('sidebarCollapsed', false);
  });

  themeToggleCollapsed.addEventListener('click', () => {
    toggleTheme();
  });

  function isMobile() {
    return window.innerWidth <= 768;
  }

  function toggleMobileSidebar() {
    if (!isMobile()) return;
    const isOpen = sidebar.classList.contains('mobile-open');
    if (isOpen) {
      closeMobileSidebar();
    } else {
      sidebar.classList.add('mobile-open');
      document.body.classList.add('sidebar-open');
    }
  }

  function closeMobileSidebar() {
    sidebar.classList.remove('mobile-open');
    document.body.classList.remove('sidebar-open');
  }

  if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleMobileSidebar();
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
      closeMobileSidebar();
    });
  }

  window.addEventListener('resize', () => {
    if (!isMobile()) {
      closeMobileSidebar();
    }
  });

  let lastScrollY = 0;
  let scrollTimeout = null;
  
  window.addEventListener('scroll', () => {
    if (!isMobile()) return;
    const currentScrollY = window.scrollY;
    if (mobileMenuBtn) {
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        mobileMenuBtn.classList.add('hidden');
      } else {
        mobileMenuBtn.classList.remove('hidden');
      }
    }
    lastScrollY = currentScrollY;
    
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      if (mobileMenuBtn) {
        mobileMenuBtn.classList.remove('hidden');
      }
    }, 1000);
  });

  function toggleTheme() {
    document.body.classList.toggle('dark');
    localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    updateThemeIcons();
    
    if (typeof mermaid !== 'undefined' && document.querySelector('.mermaid')) {
      const isDark = document.body.classList.contains('dark');
      mermaid.initialize({
        startOnLoad: true,
        theme: isDark ? 'dark' : 'default'
      });
      mermaid.run({
        querySelector: '.mermaid'
      });
    }
  }

  function updateThemeIcons() {
    const isDark = document.body.classList.contains('dark');
    const sunCircle = '<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>';
    const moonCircle = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
    
    [themeToggle, themeToggleCollapsed].forEach(btn => {
      const svg = btn.querySelector('svg');
      svg.innerHTML = isDark ? moonCircle : sunCircle;
    });
  }

  function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    const savedSidebarCollapsed = localStorage.getItem('sidebarCollapsed');
    
    if (savedTheme === 'dark') {
      document.body.classList.add('dark');
    }
    
    updateThemeIcons();
    
    if (savedSidebarCollapsed === 'true') {
      sidebar.classList.add('collapsed');
      sidebarToggle.querySelector('svg path').setAttribute('d', 'M9 18l6-6-6-6');
      sidebarToggle.title = '展开侧边栏';
    }
  }

  window.loadDoc = function(path) {
    const url = `docs/${path}`;
    viewer.innerHTML = '<p>加载中...</p>';
    
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error('文件不存在: ' + path);
        return r.text();
      })
      .then(content => {
        const isHtml = path.endsWith('.html');
        if (isHtml) {
          viewer.innerHTML = content;
        } else {
          viewer.innerHTML = renderContent(content);
        }
        window.location.hash = path;
        window.scrollTo({top: 0, behavior: 'smooth'});
        
        if (isMobile()) {
          closeMobileSidebar();
        }
        
        if (typeof mermaid !== 'undefined' && document.querySelector('.mermaid')) {
          mermaid.run();
        }
      })
      .catch(err => {
        console.log('[App] ' + err.message);
        viewer.innerHTML = `<p>文件不存在: ${path}</p>`;
      });
  };

  function renderContent(text) {
    const lines = text.split('\n');
    const html = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      if (!trimmed) {
        html.push('<br>');
        continue;
      }
      
      if (trimmed.startsWith('# ')) {
        html.push(`<h1>${escapeHtml(trimmed.substring(2))}</h1>`);
      } else if (trimmed.startsWith('## ')) {
        html.push(`<h2>${escapeHtml(trimmed.substring(3))}</h2>`);
      } else if (trimmed.startsWith('### ')) {
        html.push(`<h3>${escapeHtml(trimmed.substring(4))}</h3>`);
      } else if (trimmed.startsWith('- ')) {
        html.push(`<li>${escapeHtml(trimmed.substring(2))}</li>`);
      } else if (/^\d+\.\s/.test(trimmed)) {
        html.push(`<li>${escapeHtml(trimmed.replace(/^\d+\.\s*/, ''))}</li>`);
      } else if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        html.push(`<p>${escapeHtml(trimmed)}</p>`);
      } else if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        html.push(`<strong>${escapeHtml(trimmed.substring(2, trimmed.length - 2))}</strong>`);
      } else {
        html.push(`<p>${escapeHtml(trimmed)}</p>`);
      }
    }
    
    return html.join('\n');
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function handleHash() {
    const hash = window.location.hash.slice(1);
    console.log('[Hash] hash:', hash, ', config:', config, ', home_page:', config ? config.home_page : null);
    if (hash) {
      window.loadDoc(hash);
    } else if (config && config.home_page) {
      console.log('[Hash] 加载首页:', config.home_page);
      window.loadDoc(config.home_page);
    }
  }

  backToTop.addEventListener('click', () => {
    window.scrollTo({top: 0, behavior: 'smooth'});
  });

  window.addEventListener('scroll', () => {
    if (window.scrollY > 200) {
      backToTop.style.display = 'block';
    } else {
      backToTop.style.display = 'none';
    }
  });

  if (window.scrollY > 200) {
    backToTop.style.display = 'block';
  }

  window.addEventListener('hashchange', handleHash);

  loadConfig().then(() => {
    loadSidebar();
    handleHash();
    initTheme();
    
    if (typeof mermaid !== 'undefined') {
      const isDark = document.body.classList.contains('dark');
      mermaid.initialize({
        startOnLoad: true,
        theme: isDark ? 'dark' : 'default'
      });
    }
  });
})();
