/**
 * Family Switcher Component
 * Provides a dropdown to switch between families with visual indication of active family
 */

const FamilySwitcher = {
  currentActiveFamilyId: null,
  families: [],
  token: localStorage.getItem('token'),
  API_BASE: '/api',

  /**
   * Initialize the family switcher
   */
  async init() {
    await this.loadFamilies();
    this.setupEventListeners();
    this.updateDisplay();
  },

  /**
   * Load families and active family
   */
  async loadFamilies() {
    try {
      // Load all families
      const familiesResponse = await fetch(`${this.API_BASE}/families`, {
        headers: { Authorization: `Bearer ${this.token}` },
      });

      if (familiesResponse.ok) {
        this.families = await familiesResponse.json();
      }

      // Load active family
      try {
        const activeResponse = await fetch(`${this.API_BASE}/user/active-family`, {
          headers: { Authorization: `Bearer ${this.token}` },
        });

        if (activeResponse.ok) {
          const activeFamily = await activeResponse.json();
          this.currentActiveFamilyId = activeFamily.id;
        }
      } catch (error) {
        // No active family set
        this.currentActiveFamilyId = null;
      }
    } catch (error) {
      console.error('Error loading families:', error);
    }
  },

  /**
   * Setup event listeners for the switcher
   */
  setupEventListeners() {
    const toggleBtn = document.getElementById('family-switcher-toggle');
    const closeBtn = document.getElementById('family-switcher-close');
    const backdrop = document.getElementById('family-switcher-backdrop');

    if (toggleBtn) {
      toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggle();
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.close();
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', () => this.close());
    }

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.close();
      }
    });
  },

  /**
   * Update the display of the switcher
   */
  updateDisplay() {
    const buttonText = document.getElementById('family-switcher-text');
    const itemsContainer = document.getElementById('family-switcher-items');

    if (!buttonText || !itemsContainer) return;

    // Update button text
    if (this.currentActiveFamilyId) {
      const activeFamily = this.families.find(f => f.id === this.currentActiveFamilyId);
      if (activeFamily) {
        buttonText.textContent = activeFamily.name;
      }
    } else {
      buttonText.textContent = 'Personal';
    }

    // Update menu items
    itemsContainer.innerHTML = '';

    // Personal option
    const personalItem = document.createElement('button');
    personalItem.className =
      'w-full text-left px-4 py-3 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors flex items-center justify-between group ' +
      (this.currentActiveFamilyId === null ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white');
    personalItem.innerHTML = `
      <div>
        <p class="font-medium">Personal</p>
        <p class="text-xs opacity-70">Private transactions</p>
      </div>
      ${this.currentActiveFamilyId === null ? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>' : ''}
    `;
    personalItem.disabled = this.currentActiveFamilyId === null;
    if (this.currentActiveFamilyId !== null) {
      personalItem.style.cursor = 'pointer';
      personalItem.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchToPersonal();
      });
    }
    itemsContainer.appendChild(personalItem);

    // Family separator
    if (this.families.length > 0) {
      const separator = document.createElement('div');
      separator.className = 'border-t border-gray-200 dark:border-slate-700 my-2';
      itemsContainer.appendChild(separator);
    }

    // Family options
    this.families.forEach(family => {
      const item = document.createElement('button');
      const isActive = family.id === this.currentActiveFamilyId;
      item.className =
        'w-full text-left px-4 py-3 hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors flex items-center justify-between group ' +
        (isActive
          ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 cursor-not-allowed opacity-60'
          : 'text-gray-900 dark:text-white');
      item.innerHTML = `
        <div>
          <p class="font-medium">${family.name}</p>
          <p class="text-xs opacity-70">${family.members?.length || 0} members</p>
        </div>
        ${isActive ? '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>' : ''}
      `;
      item.disabled = isActive;
      if (!isActive) {
        item.style.cursor = 'pointer';
        item.addEventListener('click', (e) => {
          e.preventDefault();
          this.switchToFamily(family.id);
        });
      }
      itemsContainer.appendChild(item);
    });
  },

  /**
   * Toggle the switcher dropdown
   */
  toggle() {
    const dropdown = document.getElementById('family-switcher-dropdown');
    if (dropdown) {
      dropdown.classList.toggle('hidden');
      document.getElementById('family-switcher-backdrop')?.classList.toggle('hidden');
    }
  },

  /**
   * Open the switcher dropdown
   */
  open() {
    const dropdown = document.getElementById('family-switcher-dropdown');
    if (dropdown && dropdown.classList.contains('hidden')) {
      dropdown.classList.remove('hidden');
      document.getElementById('family-switcher-backdrop')?.classList.remove('hidden');
    }
  },

  /**
   * Close the switcher dropdown
   */
  close() {
    const dropdown = document.getElementById('family-switcher-dropdown');
    if (dropdown && !dropdown.classList.contains('hidden')) {
      dropdown.classList.add('hidden');
      document.getElementById('family-switcher-backdrop')?.classList.add('hidden');
    }
  },

  /**
   * Switch to a specific family
   */
  async switchToFamily(familyId) {
    try {
      const response = await fetch(`${this.API_BASE}/families/${familyId}/set-active`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${this.token}` },
      });

      if (response.ok) {
        this.currentActiveFamilyId = familyId;
        this.updateDisplay();
        this.close();
        // Reload page to reflect family-scoped data
        window.location.reload();
      } else {
        alert('Failed to switch family');
      }
    } catch (error) {
      console.error('Error switching family:', error);
      alert('Error switching family');
    }
  },

  /**
   * Switch to personal (no family)
   * Clears active family by calling the clear endpoint
   */
  async switchToPersonal() {
    try {
      // Try the clear-active endpoint first (if implemented)
      try {
        const clearResponse = await fetch(`${this.API_BASE}/families/clear-active`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${this.token}` },
        });
        
        if (clearResponse.ok) {
          this.currentActiveFamilyId = null;
          this.updateDisplay();
          this.close();
          window.location.reload();
          return;
        }
      } catch (clearError) {
        console.log('Clear endpoint not available, trying alternative approach');
      }
      
      // Fallback: Just update UI and reload
      // The backend will see no family_id in the filter and show personal transactions
      console.warn('Using client-side personal mode switch (clear endpoint not implemented)');
      this.currentActiveFamilyId = null;
      this.updateDisplay();
      this.close();
      
      // Still reload to ensure fresh data
      window.location.reload();
    } catch (error) {
      console.error('Error switching to personal mode:', error);
      alert('Error switching to personal mode');
    }
  },

  /**
   * Refresh the switcher (call after families change)
   */
  async refresh() {
    await this.loadFamilies();
    this.updateDisplay();
  },
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => FamilySwitcher.init());
} else {
  FamilySwitcher.init();
}
