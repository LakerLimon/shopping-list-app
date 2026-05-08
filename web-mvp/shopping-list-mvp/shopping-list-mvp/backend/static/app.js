const state = {
  access: localStorage.getItem("access") || "",
  refresh: localStorage.getItem("refresh") || "",
  user: JSON.parse(localStorage.getItem("user") || "null"),
  lists: [],
  selectedList: null,
};

const $ = (id) => document.getElementById(id);

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2800);
}

function authHeaders() {
  return state.access ? { Authorization: `Bearer ${state.access}` } : {};
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = data.detail || data.non_field_errors?.join(" ") || JSON.stringify(data);
    throw new Error(detail || "Ошибка запроса");
  }
  return data;
}

function saveAuth(payload) {
  state.access = payload.access;
  state.refresh = payload.refresh;
  state.user = payload.user;
  localStorage.setItem("access", state.access);
  localStorage.setItem("refresh", state.refresh);
  localStorage.setItem("user", JSON.stringify(state.user));
  renderAuth();
}

function clearAuth() {
  state.access = "";
  state.refresh = "";
  state.user = null;
  state.lists = [];
  state.selectedList = null;
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
  renderAuth();
}

function renderAuth() {
  const loggedIn = Boolean(state.access);
  $("authSection").classList.toggle("hidden", loggedIn);
  $("workSection").classList.toggle("hidden", !loggedIn);
  $("logoutBtn").classList.toggle("hidden", !loggedIn);
  if (loggedIn) {
    loadLists();
    loadNotifications();
  }
}

async function register() {
  const email = $("email").value.trim();
  const password = $("password").value;
  const data = await api("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  saveAuth(data);
  toast("Аккаунт создан");
}

async function login() {
  const email = $("email").value.trim();
  const password = $("password").value;
  const data = await api("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  saveAuth(data);
  toast("Вход выполнен");
}

async function loadLists() {
  state.lists = await api("/api/lists/");
  renderLists();
}

function renderLists() {
  const root = $("lists");
  root.innerHTML = "";
  if (!state.lists.length) {
    root.innerHTML = `<p class="muted">Списков пока нет.</p>`;
    return;
  }
  state.lists.forEach((list) => {
    const item = document.createElement("div");
    item.className = "item";
    item.innerHTML = `
      <div>
        <strong>${escapeHtml(list.name)}</strong>
        <small>роль: ${list.role} · участников: ${list.members_count}</small>
      </div>
      <div class="actions"><button class="secondary" data-open-list="${list.id}">Открыть</button></div>
    `;
    root.appendChild(item);
  });
}

async function createList(event) {
  event.preventDefault();
  const name = $("listName").value.trim();
  if (!name) return;
  const list = await api("/api/lists/", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  $("listName").value = "";
  toast("Список создан");
  await loadLists();
  await openList(list.id);
}

async function openList(id) {
  const list = state.lists.find((item) => item.id === Number(id)) || await api(`/api/lists/${id}/`);
  state.selectedList = list;
  $("selectedListCard").classList.remove("hidden");
  $("selectedListTitle").textContent = list.name;
  $("inviteResult").classList.add("hidden");
  await loadProducts();
  await loadHistory();
}

async function createInvite() {
  if (!state.selectedList) return;
  const invite = await api(`/api/lists/${state.selectedList.id}/invite/`, { method: "POST" });
  const el = $("inviteResult");
  el.innerHTML = `Код приглашения: <strong>${invite.code}</strong><br>Ссылка: ${invite.invite_url}`;
  el.classList.remove("hidden");
  toast("Приглашение создано");
}

async function acceptInvite(event) {
  event.preventDefault();
  const code = $("inviteCode").value.trim();
  if (!code) return;
  const result = await api(`/api/invitations/${code}/accept/`, { method: "POST" });
  $("inviteCode").value = "";
  toast(result.status === "joined" ? "Вы присоединились к списку" : "Вы уже в этом списке");
  await loadLists();
  await openList(result.list_id);
}

async function addProduct(event) {
  event.preventDefault();
  if (!state.selectedList) return;
  const payload = {
    name: $("productName").value.trim(),
    quantity: $("productQty").value || "1",
    unit: $("productUnit").value.trim() || "шт",
    estimated_price: $("productPrice").value || null,
    category_name: $("productCategory").value.trim(),
    comment: $("productComment").value.trim(),
  };
  if (!payload.name) return;
  await api(`/api/lists/${state.selectedList.id}/products/`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  $("productForm").reset();
  $("productQty").value = "1";
  $("productUnit").value = "шт";
  toast("Товар добавлен");
  await loadProducts();
  await loadNotifications();
}

async function loadProducts() {
  if (!state.selectedList) return;
  const products = await api(`/api/lists/${state.selectedList.id}/products/`);
  renderProducts(products, "products", false);
}

async function loadHistory() {
  if (!state.selectedList) return;
  const products = await api(`/api/lists/${state.selectedList.id}/history/`);
  renderProducts(products, "history", true);
}

function renderProducts(products, rootId, history) {
  const root = $(rootId);
  root.innerHTML = "";
  if (!products.length) {
    root.innerHTML = `<p class="muted">${history ? "История пуста." : "Активных товаров нет."}</p>`;
    return;
  }
  products.forEach((product) => {
    const item = document.createElement("div");
    item.className = "item";
    const category = product.category ? ` · ${escapeHtml(product.category.name)}` : "";
    const price = product.estimated_price ? ` · ${product.estimated_price} ₽` : "";
    const who = product.is_bought && product.bought_by ? `Купил: ${escapeHtml(product.bought_by.email)}` : `Добавил: ${escapeHtml(product.added_by?.email || "—")}`;
    item.innerHTML = `
      <div>
        <strong>${escapeHtml(product.name)}</strong>
        <small>${product.quantity} ${escapeHtml(product.unit)}${category}${price}</small>
        <small>${escapeHtml(product.comment || "")}</small>
        <small>${who}</small>
      </div>
      <div class="actions">
        ${history ? "" : `<button data-buy-product="${product.id}">Куплено</button>`}
        ${history ? "" : `<button class="secondary" data-edit-product="${product.id}">Изменить</button>`}
        ${history ? "" : `<button class="danger" data-delete-product="${product.id}">Удалить</button>`}
      </div>
    `;
    root.appendChild(item);
  });
}

async function buyProduct(id) {
  await api(`/api/products/${id}/buy/`, { method: "POST" });
  toast("Товар перенесён в историю");
  await loadProducts();
  await loadHistory();
  await loadNotifications();
}

async function deleteProduct(id) {
  await api(`/api/products/${id}/`, { method: "DELETE" });
  toast("Товар удалён");
  await loadProducts();
  await loadNotifications();
}

async function editProduct(id) {
  const name = prompt("Новое название товара:");
  if (!name) return;
  await api(`/api/products/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
  toast("Товар изменён");
  await loadProducts();
}

async function loadNotifications() {
  const notifications = await api("/api/notifications/");
  const root = $("notifications");
  root.innerHTML = "";
  if (!notifications.length) {
    root.innerHTML = `<p class="muted">Уведомлений пока нет.</p>`;
    return;
  }
  notifications.forEach((notification) => {
    const item = document.createElement("div");
    item.className = "item";
    item.innerHTML = `
      <div>
        <strong>${escapeHtml(notification.message)}</strong>
        <small>${escapeHtml(notification.shopping_list_name)} · ${new Date(notification.created_at).toLocaleString()}</small>
      </div>
      <small>${notification.is_read ? "прочитано" : "новое"}</small>
    `;
    root.appendChild(item);
  });
}

async function markNotificationsRead() {
  await api("/api/notifications/", { method: "PATCH", body: JSON.stringify({}) });
  await loadNotifications();
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.addEventListener("click", async (event) => {
  const target = event.target;
  try {
    if (target.dataset.openList) await openList(target.dataset.openList);
    if (target.dataset.buyProduct) await buyProduct(target.dataset.buyProduct);
    if (target.dataset.deleteProduct) await deleteProduct(target.dataset.deleteProduct);
    if (target.dataset.editProduct) await editProduct(target.dataset.editProduct);
  } catch (error) {
    toast(error.message);
  }
});

$("registerBtn").addEventListener("click", () => register().catch((error) => toast(error.message)));
$("loginBtn").addEventListener("click", () => login().catch((error) => toast(error.message)));
$("logoutBtn").addEventListener("click", clearAuth);
$("createListForm").addEventListener("submit", (event) => createList(event).catch((error) => toast(error.message)));
$("acceptInviteForm").addEventListener("submit", (event) => acceptInvite(event).catch((error) => toast(error.message)));
$("productForm").addEventListener("submit", (event) => addProduct(event).catch((error) => toast(error.message)));
$("inviteBtn").addEventListener("click", () => createInvite().catch((error) => toast(error.message)));
$("readNotificationsBtn").addEventListener("click", () => markNotificationsRead().catch((error) => toast(error.message)));

const invitePathMatch = location.pathname.match(/^\/invite\/([0-9a-f-]+)\/?$/i);
if (invitePathMatch) {
  const inviteInput = $("inviteCode");
  if (inviteInput) inviteInput.value = invitePathMatch[1];
}

renderAuth();
