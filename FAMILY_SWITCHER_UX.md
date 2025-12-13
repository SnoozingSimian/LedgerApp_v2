# Family Switcher UX Improvements

## Overview
Implemented a new family switcher component that provides better UX for managing families across all screens. Users can now:
- See which family is currently active
- Quickly switch between families from any page
- Visual indication of the active family (disabled/greyed out)
- Clear distinction between personal and family transactions

---

## ⚠️ CRITICAL: Personal Mode vs Families

### Personal Mode - NOT a Family
- **Personal is NOT a database family** - it represents the absence of an active family
- Data stored with `family_id = NULL`
- Displayed in UI as an option but is NOT created in the families table
- No members can be added (it's single-user mode)
- Used for personal transactions, budgets, and credit sources
- Always available as the default mode

### Shareable Families - ARE Database Records
- **ARE stored in the families table** - only actual family groups
- Members can be invited and added
- Can transfer data from personal mode via import feature
- Data stored with `family_id = [family.id]`
- Listed in family switcher dropdown with member count

### ⚠️ CONSTRAINT TO ENFORCE
```
There should NEVER be a family with name="Personal" in the database.
If one exists, it should be deleted and this design should be reviewed.
```

If users see:
- A "Personal" family in the families list
- A "Personal" family with no members
- A "Personal" family with empty data

This is a **BUG** - Personal should not be a family.

---

## Debugging: Identify Personal Family Issue

If there's a "Personal" family showing up:

### Step 1: Check Database
```sql
SELECT id, name, created_by, created_at FROM families WHERE name = 'Personal';
```

If results show a Personal family:
- **This is the bug** - Personal should not exist as a family
- Delete it: `DELETE FROM families WHERE name = 'Personal';`

### Step 2: Check Where It's Created
Search codebase for:
```
name="Personal"
name='Personal'
"Personal"
'Personal'
family.name = 'Personal'
Family(name='Personal'
```

Should find ONLY:
- This documentation
- Frontend JS showing it in UI
- Tests that mention it

Should NOT find:
- Code that creates it in the database
- Code that imports it
- Code that assigns it automatically

### Step 3: Frontend Verification
Open browser console and run:
```javascript
FamilySwitcher.families.forEach(f => console.log(`Family: ${f.name} (${f.members?.length || 0} members)`));
```

Should NOT show any family named "Personal"

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
- Lists ONLY actual shareable families (from database)
- Shows member count for each family
- Visual hierarchy with checkmarks for active selection

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
- Loads all families and active family from backend
- Sets up event listeners
- Updates display

#### Key Methods

**`loadFamilies()`**
- Fetches user's families from `/api/families` (actual families only)
- Fetches active family from `/api/user/active-family` (may return 404 if Personal mode)
- Handles error if no active family (defaults to Personal mode)
- **Important**: Only actual families are returned from `/api/families`

**`updateDisplay()`**
- Updates button text with active family name or "Personal"
- Renders dropdown menu items:
  - "Personal" option at top (hardcoded, not from API)
  - Separator line if families exist
  - Actual families listed below (from API response)
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
- Reloads page to show personal transactions (family_id = NULL)
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
    <!-- Personal option (hardcoded, not a family) -->
    <!-- Family options (only from API) -->
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
5. No other family options visible (families list is empty)
6. All transactions/budgets/credit sources are personal (family_id = NULL)

### Scenario 2: Create Family
1. User creates "Smith Family" (actual shareable family)
2. User is added as admin member to families table
3. User can invite other members
4. Family appears in switcher dropdown (NOT Personal family, real family)
5. Shows member count
6. User can switch to Smith Family
7. Data is family-scoped (family_id = [family.id])

### Scenario 3: Switch Between Modes
1. User in Smith Family mode
2. Clicks switcher button
3. Options shown:
   - Personal (clickable, from hardcoded UI)
   - Smith Family (disabled, has checkmark, from API)
   - Other families (clickable, from API)
4. User clicks "Personal"
5. → Page reloads with personal transactions only
6. Switcher shows "Personal" again

### Scenario 4: Import Data
1. User in Personal mode with existing data
2. Creates "Family A" for sharing
3. Uses import feature during creation to copy personal data to Family A
4. Personal data remains in personal mode (family_id = NULL)
5. Family A gets copy of the data (family_id = family_a.id)
6. User can switch between Personal and Family A

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
- **Returns ONLY actual families** (NEVER returns a "Personal" family)
- Does NOT include "Personal" (Personal is not a family)
- Each family includes: id, name, members list
- Returns empty array [] if user has no families

**GET `/api/user/active-family`**
- Returns currently active family object
- Returns 404 if no active family (user is in Personal mode)
- Handled gracefully - component switches to Personal mode

**POST `/api/families/{familyId}/set-active`**
- Sets family as active
- Updates user.active_family_id in database
- Returns family id and success message
- Must be member of family (enforced by backend)

**POST `/api/families/clear-active`**
- Clears active family
- Sets user.active_family_id = NULL
- Switches user to Personal mode
- Returns success message with family_id: null

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

### Frontend Correctly Handles Personal
- "Personal" is hardcoded in the UI dropdown
- It is NOT fetched from any API
- It is NOT in the families array
- It represents `active_family_id = NULL` state

### Backend Should Enforce
- `/api/families` returns ONLY actual families (not Personal)
- No code creates a family named "Personal"
- Personal mode is represented by `active_family_id = NULL`
- No members table entry for Personal

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

### Design Clarification
- **Commit SHA**: 80b921e15d89ffa04ab8e290551ec840283f4030
- **File**: `FAMILY_SWITCHER_UX.md`
- **Message**: Update: Clarify that Personal is NOT a family, only shareable families should be listed

---

## Testing Checklist

- [ ] Family switcher loads on page visit
- [ ] Current mode is displayed correctly ("Personal" or Family name)
- [ ] Dropdown opens/closes on button click
- [ ] Dropdown closes on ESC key press
- [ ] Dropdown closes on backdrop click
- [ ] Currently active mode is highlighted
- [ ] Currently active mode is disabled/greyed out
- [ ] Cannot click currently active mode
- [ ] Switching to different family reloads page
- [ ] Data reflects new family scope after reload
- [ ] "Personal" option is always available
- [ ] **NO "Personal" family in the list** (only in hardcoded menu)
- [ ] **NO "Personal" entry in families table** (verify with SELECT)
- [ ] Only actual families are listed from API
- [ ] Only families with members are shown (user is member)
- [ ] Dark mode styling is correct
- [ ] Mobile responsive on all sizes
- [ ] Works on iPhone notch/safe areas
- [ ] No console errors
- [ ] Browser console: `FamilySwitcher.families` should NOT contain any family named "Personal"

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
