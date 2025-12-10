// Dark Mode Management
class DarkModeManager {
  constructor() {
    this.isDark = localStorage.getItem('darkMode') === 'true' || 
                  window.matchMedia('(prefers-color-scheme: dark)').matches;
    this.init();
  }

  init() {
    // Apply initial dark mode state
    this.setDarkMode(this.isDark);
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      this.setDarkMode(e.matches);
    });
  }

  setDarkMode(isDark) {
    this.isDark = isDark;
    localStorage.setItem('darkMode', isDark);
    
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  toggle() {
    this.setDarkMode(!this.isDark);
  }

  get isDarkMode() {
    return this.isDark;
  }
}

// Initialize on page load
const darkModeManager = new DarkModeManager();
