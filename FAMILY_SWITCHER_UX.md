# Family Switcher UX Improvements

## Overview
Implemented a new family switcher component that provides better UX for managing families across all screens. Users can now:
- See which family is currently active
- Quickly switch between families from any page
- Visual indication of the active family (disabled/greyed out)
- Clear distinction between personal and family transactions

---

## IMPORTANT: Personal Mode vs Families

### Personal Mode
- **NOT a family** - It's the absence of a family selection
- Used for single-user operations (personal transactions, budgets, credit sources)
- Data stored with `family_id = NULL`
- No members can be added
- **Always available** - This is the default mode for all users
- Accessible via dropdown menu showing "Personal"

### Shareable Families
- **ARE families** - Created by the user to share expenses
- Members can be invited and added
- Can transfer data from personal mode via import feature
- Data stored with `family_id = [family.id]`
- Listed in family switcher dropdown
- Shown with member count

---

## Features Implemented

### 1. **Persistent Family Switcher in Header**
- Located in the header on every page (Dashboard, Transactions, Budgets, etc.)
- Displays the currently active family name OR "Personal"
- Dropdown icon indicates more options available
- Responsive design works on mobile and desktop

### 2. **Family Selection Dropdown**
- Click the switcher button to open dropdown menu
- Shows "Personal" option (for personal/unscoped transactions) - NOT a family
- Lists ONLY actual shareable families (not Personal)
- Visual hierarchy with checkmarks for active selection
- Shows member count for each family

### 3. **Smart Disabling of Current Mode**
- Currently active mode is highlighted in blue
- Option is disabled/greyed out (opacity 60%)
- Cannot click to select an already-active mode
- Clear visual feedback with checkmark icon

### 4. **Automatic Page Reload**
- When switching families or modes, page automatically reloads
- Ensures all data is family-scoped correctly
- User sees updated transactions, budgets, credit sources, etc.

---

## Component Architecture

### JavaScript Module: `FamilySwitcher` (`/static/family-switcher.js`)

The component is a self-contained JavaScript module with the following methods:

#### Initialization
```javascript
FamilySwitcher.init()
```
- Loads all families and active family
- Sets up event listeners
- Updates display

#### Key Methods

**`loadFamilies()`**
- Fetches user's families from `/api/families`
- Fetches active family from `/api/user/active-family`
- Handles error if no active family (returns to Personal mode)
- **Important**: Only actual families are returned from `/api/families`, never "Personal"

**`updateDisplay()`**
- Updates button text with active family name or "Personal"
- Renders dropdown menu items:
  - "Personal" option at top (always available)
  - Actual families listed below separator
- Disables currently active mode
- Shows checkmark for active selection

**`switchToFamily(familyId)`**
- POST to `/api/families/{familyId}/set-active`
- Sets as active family
- Reloads page to fetch scoped data
- Must be member of family (enforced by backend)

**`switchToPersonal()`**
- POST to `/api/families/clear-active`
- Clears active family (sets `active_family_id = null`)
- Reloads page to show personal transactions
- Returns to personal-only mode

**`toggle()`, `open()`, `close()`**
- Manage dropdown visibility
- Keyboard support (ESC to close)
- Click outside to close

---

## HTML Integration

### Header Implementation
```html
<!-- Family Switcher Button -->
<button id="family-switcher-toggle" class="...">
  <svg><!-- Family icon --></svg>
  <span id="family-switcher-text">Loading...</span>
  <svg><!-- Chevron down --></svg>
</button>

<!-- Dropdown Menu -->
<div id="family-switcher-dropdown" class="hidden ...">
  <div id="family-switcher-items">
    <!-- Personal option (always shown) -->
    <!-- Family options (only actual families) -->
  </div>
</div>

<!-- Backdrop (for closing) -->
<div id="family-switcher-backdrop" class="hidden ..."></div>
```

### Script Include
```html
<script src="/static/family-switcher.js"></script>
```

---

## Updated Templates

### Dashboard (`templates/dashboard.html`)
✅ Added family switcher in header  
✅ Script included for initialization  
✅ Maintains existing functionality  

### Templates Needing Updates (Same Changes)
- `templates/transactions.html`
- `templates/budgets.html`
- `templates/credit_sources.html`

Each should include:
1. Family switcher HTML in header (after title)
2. `<script src="/static/family-switcher.js"></script>` before closing body

---

## User Experience Flow

### Scenario 1: Personal Mode (Default)
1. New user signs up
2. No families created yet
3. Switcher shows "Personal"
4. "Personal" option is disabled/highlighted
5. No other family options visible
6. All transactions/budgets/credit sources are personal (family_id = NULL)

### Scenario 2: Create Family
1. User creates "Smith Family" (shareable family)
2. User is added as admin member
3. User can invite other members
4. Family appears in switcher dropdown (with member count)
5. User can switch to Smith Family
6. Data is family-scoped

### Scenario 3: Switch Between Modes
1. User in Smith Family mode
2. Clicks switcher button
3. Options shown:
   - Personal (clickable)
   - Smith Family (disabled, has checkmark)
   - Other families (clickable)
4. User clicks "Personal"
5. → Page reloads with personal transactions only
6. Switcher shows "Personal" again

### Scenario 4: Import Data
1. User in Personal mode with existing data
2. Creates "Family A" for sharing
3. Uses import feature during creation to copy personal data to Family A
4. Personal data remains in personal mode
5. Family A gets copy of the data
6. User can switch between modes

---

## Visual States

### Button States
- **Inactive**: Gray background, normal cursor
- **Hover**: Slightly darker background, pointer cursor
- **Active**: Part of dropdown display

### Menu Item States

**Active Mode Item (Personal or Family)**
- Blue background (`bg-blue-50 dark:bg-blue-900/20`)
- Blue text (`text-blue-600 dark:text-blue-400`)
- Checkmark icon ✓
- Reduced opacity (60%)
- Disabled cursor (`cursor-not-allowed`)
- Cannot be clicked

**Inactive Mode Item**
- White/slate background
- Normal text color
- No icon
- Full opacity
- Pointer cursor
- Clickable

**Hover State**
- Gray background (`hover:bg-gray-100 dark:hover:bg-slate-700`)
- Transition smooth

---

## Dark Mode Support

All colors use Tailwind dark mode utilities:
- Button: `dark:bg-slate-700`, `dark:hover:bg-slate-600`, `dark:text-slate-300`
- Dropdown: `dark:bg-slate-800`, `dark:border-slate-700`, `dark:bg-slate-900`
- Text: `dark:text-white`, `dark:text-slate-400`
- States: `dark:bg-blue-900/20`, `dark:text-blue-400`

---

## API Integration

### Endpoints Used

**GET `/api/families`**
- Returns list of shareable families user is member of
- Does NOT include "Personal" (Personal is not a family)
- Each family includes: id, name, members list
- Returns empty array if user has no families

**GET `/api/user/active-family`**
- Returns currently active family
- Returns 404 if no active family (user is in Personal mode)
- Handled gracefully in component

**POST `/api/families/{familyId}/set-active`**
- Sets family as active
- Updates user.active_family_id in database
- Returns family id and success message

**POST `/api/families/clear-active`**
- Clears active family
- Sets user.active_family_id = NULL
- Switches user to Personal mode
- Returns success message

---

## Setup Instructions

### Adding to New Templates

1. Add family switcher HTML to header (after page title):
```html
<!-- Family Switcher -->
<div class="relative">
  <button id="family-switcher-toggle" class="ml-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-slate-300 text-sm font-medium transition-colors flex items-center gap-2">
    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 12a4 4 0 100-8 4 4 0 000 8zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
    <span id="family-switcher-text">Loading...</span>
    <svg class="w-4 h-4 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
  </button>

  <!-- Dropdown menu - see dashboard.html for full HTML -->
</div>
```

2. Add script include before closing `</body>`:
```html
<script src="/static/family-switcher.js"></script>
```

3. No additional configuration needed - component auto-initializes

---

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- ES6+ JavaScript
- Fetch API
- CSS Grid/Flexbox

---

## Key Implementation Notes

### Personal is NOT a Family
- "Personal" is shown in the switcher but it's NOT a family from the database
- It represents `family_id = NULL` state
- No members can be invited to Personal mode
- Data is filtered by `family_id IS NULL` when in Personal mode

### Family Creation & Sharing
- Only actual shareable families appear in the list
- User must create a family via "Create Family" button to share expenses
- Import feature allows copying personal data to new families
- Personal and family data are kept separate by `family_id` column

### Data Isolation
- Personal data: `family_id = NULL`
- Family data: `family_id = [specific family.id]`
- Queries filter by active_family_id to show correct scope

---

## Future Enhancements

Possible improvements:
- [ ] Keyboard navigation (arrow keys in dropdown)
- [ ] Search family by name if many families
- [ ] Show badge with member count
- [ ] Animate dropdown opening/closing
- [ ] Add "Manage Families" quick link in dropdown
- [ ] Remember last used family across sessions

---

## Commits

### Family Switcher Component
- **Commit SHA**: a9c6bc763c17e792529d12ae6861b5c2c08cb046
- **File**: `static/family-switcher.js`
- **Message**: Add family switcher component with improved UX

### Dashboard Update
- **Commit SHA**: cee2ba577fdb6c7e7add027abe96fa702b463b53
- **File**: `templates/dashboard.html`
- **Message**: Add family switcher to dashboard header

### Personal Mode Fix (Frontend)
- **Commit SHA**: 0aef21abfa78e6bc5730ce319ca44c16c7c70d27
- **File**: `static/family-switcher.js`
- **Message**: Fix: Handle Personal mode switching without requiring API endpoint

### Personal Mode Fix (Backend)
- **Commit SHA**: 491efca66404d0209c2b55b1db474c12d902a472
- **File**: `app/routers/family.py`
- **Message**: Add clear-active endpoint to allow switching back to personal mode

---

## Testing Checklist

- [ ] Family switcher loads on page visit
- [ ] Current mode is displayed correctly (Personal or Family name)
- [ ] Dropdown opens/closes on button click
- [ ] Dropdown closes on ESC key press
- [ ] Dropdown closes on backdrop click
- [ ] Currently active mode is highlighted
- [ ] Currently active mode is disabled/greyed out
- [ ] Cannot click currently active mode
- [ ] Switching to different family reloads page
- [ ] Data reflects new family scope after reload
- [ ] "Personal" option is always available
- [ ] Only actual families are listed (NO "Personal" family in list)
- [ ] Only family members are shown (current user is member)
- [ ] Dark mode styling is correct
- [ ] Mobile responsive on all sizes
- [ ] Works on iPhone notch/safe areas
- [ ] No console errors
- [ ] No "Personal" family exists in database

---

## Files to Update

Apply the same family switcher changes to these templates:

```
templates/
├── dashboard.html          ✅ DONE
├── transactions.html       ⏳ TODO
├── budgets.html           ⏳ TODO
├── credit_sources.html    ⏳ TODO
└── families.html          (Optional - different UI for family management)
```

Each file needs:
1. Family switcher HTML in header
2. `<script src="/static/family-switcher.js"></script>` before `</body>`
