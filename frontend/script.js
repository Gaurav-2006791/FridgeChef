function getApiBaseUrl() {
  const configuredBase = window.__FRIDGE_CHEF_API_BASE__;
  if (configuredBase) {
    return configuredBase.replace(/\/$/, '');
  }

  const { protocol, hostname, port } = window.location;
  if (port === '8000') {
    return `${protocol}//${hostname}`;
  }

  return `${protocol}//${hostname}:8000`;
}

function showMessage(messageElement, type, message) {
  if (!messageElement) return;
  messageElement.className = `alert alert-${type}`;
  messageElement.textContent = message;
}

const form = document.getElementById('recipeForm');
const submitBtn = document.getElementById('submitBtn');
const loading = document.getElementById('loading');
const resultsContainer = document.querySelector('.recipe-card');

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!form.checkValidity()) {
      event.stopPropagation();
      form.classList.add('was-validated');
      return;
    }

    const payload = {
      ingredients: document.getElementById('ingredients').value.trim(),
      cuisine: document.getElementById('cuisine').value,
      meal_type: document.getElementById('mealType').value,
      diet: document.getElementById('diet').value,
      cooking_time: document.getElementById('cookingTime').value,
      spice_level: document.getElementById('spiceLevel').value,
      servings: document.getElementById('servings').value,
    };

    if (submitBtn) submitBtn.disabled = true;
    if (loading) loading.classList.remove('d-none');
    if (resultsContainer) {
      resultsContainer.innerHTML = '<h3 class="fw-bold mb-3">Your Recipe</h3><p class="text-muted">Creating a delicious recipe for you...</p>';
    }

    try {
      const response = await fetch(`${getApiBaseUrl()}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to generate recipe');
      }

      renderRecipe(data);
    } catch (error) {
      if (resultsContainer) {
        resultsContainer.innerHTML = `
          <div class="alert alert-danger fade-in" role="alert">
            <strong>Recipe generation failed.</strong><br />${error.message}
          </div>
        `;
      }
    } finally {
      if (submitBtn) submitBtn.disabled = false;
      if (loading) loading.classList.add('d-none');
    }
  });
}

const signinForm = document.getElementById('signinForm');
const signupForm = document.getElementById('signupForm');

if (signinForm) {
  signinForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const messageElement = document.getElementById('formMessage');
    const email = document.getElementById('signinEmail').value.trim();
    const password = document.getElementById('signinPassword').value;

    try {
      const response = await fetch(`${getApiBaseUrl()}/signin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sign in failed');
      }
      showMessage(messageElement, 'success', data.message || 'Signed in successfully');
      window.location.assign(`${getApiBaseUrl()}/dashboard`);
    } catch (error) {
      showMessage(messageElement, 'danger', error.message);
    }
  });
}

if (signupForm) {
  signupForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const messageElement = document.getElementById('formMessage');
    const fullName = document.getElementById('fullName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    try {
      const response = await fetch(`${getApiBaseUrl()}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email, password, confirm_password: confirmPassword }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Sign up failed');
      }
      showMessage(messageElement, 'success', data.message || 'Account created successfully');
      window.location.assign(`${getApiBaseUrl()}/dashboard`);
    } catch (error) {
      showMessage(messageElement, 'danger', error.message);
    }
  });
}

async function loadUserProfile() {
  const userNameElement = document.getElementById('userName');
  const profileNameElement = document.getElementById('profileName');
  const profileEmailElement = document.getElementById('profileEmail');

  if (!userNameElement && !profileNameElement && !profileEmailElement) return;

  try {
    const response = await fetch(`${getApiBaseUrl()}/me`, { credentials: 'include' });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Unable to load profile');

    const fullName = data.full_name || 'Chef';
    const firstName = fullName.split(' ')[0];
    if (userNameElement) userNameElement.textContent = firstName;
    if (profileNameElement) profileNameElement.textContent = fullName;
    if (profileEmailElement) profileEmailElement.textContent = data.email || 'chef@fridgechef.app';
  } catch (error) {
    if (userNameElement) userNameElement.textContent = 'Chef';
    if (profileNameElement) profileNameElement.textContent = 'Chef';
    if (profileEmailElement) profileEmailElement.textContent = 'chef@fridgechef.app';
  }
}

if (document.getElementById('userName') || document.getElementById('profileName') || document.getElementById('profileEmail')) {
  loadUserProfile();
}

function renderRecipe(recipe) {
  if (!resultsContainer) return;
  resultsContainer.className = 'recipe-card p-4 fade-in';
  resultsContainer.innerHTML = `
    <h3 class="fw-bold mb-3">${recipe.recipe_name}</h3>
    <div class="mb-3">
      <span class="recipe-pill">Cuisine: ${recipe.cuisine_style}</span>
      <span class="recipe-pill">Difficulty: ${recipe.difficulty}</span>
      <span class="recipe-pill">Servings: ${document.getElementById('servings').value}</span>
    </div>
    <div class="row g-3 mb-4">
      <div class="col-md-3"><strong>Prep</strong><br />${recipe.preparation_time}</div>
      <div class="col-md-3"><strong>Cook</strong><br />${recipe.cooking_time}</div>
      <div class="col-md-3"><strong>Calories</strong><br />${recipe.calories}</div>
      <div class="col-md-3"><strong>Protein</strong><br />${recipe.protein}</div>
    </div>
    <div class="row g-4">
      <div class="col-lg-6">
        <h5>Ingredients</h5>
        <ul>${recipe.ingredients.map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
      <div class="col-lg-6">
        <h5>Instructions</h5>
        <ol>${recipe.instructions.map((step) => `<li>${step}</li>`).join('')}</ol>
      </div>
    </div>
    <div class="row g-4 mt-2">
      <div class="col-md-6">
        <h5>Nutrition</h5>
        <p class="mb-1"><strong>Carbs:</strong> ${recipe.carbohydrates}</p>
        <p class="mb-1"><strong>Fat:</strong> ${recipe.fat}</p>
        <p class="mb-1"><strong>Calories:</strong> ${recipe.calories}</p>
      </div>
      <div class="col-md-6">
        <h5>Serving Suggestions</h5>
        <ul>${recipe.serving_suggestions.map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
    </div>
    <div class="row g-4 mt-2">
      <div class="col-md-6">
        <h5>Chef Tips</h5>
        <ul>${recipe.chef_tips.map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
      <div class="col-md-6">
        <h5>Healthy Alternatives</h5>
        <ul>${recipe.healthy_alternatives.map((item) => `<li>${item}</li>`).join('')}</ul>
      </div>
    </div>
    <div class="mt-3">
      <h5>Food Pairing</h5>
      <ul>${recipe.food_pairing.map((item) => `<li>${item}</li>`).join('')}</ul>
    </div>
  `;
}
