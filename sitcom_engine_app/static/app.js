const APP_NAME = "SkitBox";

const PAGES = {
  start: ["Start", "Ready Room"],
  templates: ["Templates", "Choose Your Sitcom"],
  guide: ["Guide", "How to Build"],
  bible: ["Bible", "Show Bible"],
  characters: ["Characters", "Cast"],
  locations: ["Locations", "Places & Props"],
  rooms: ["Rooms", "Room Map"],
  memory: ["Memory", "Canon Memory"],
  jokes: ["Jokes", "Jokes & Rules"],
  sparks: ["Sparks", "Scene Sparks"],
  generate: ["Generate", "Episode Generator"],
  tester: ["Tester", "Tester Run"],
  library: ["Library", "Episode Library"],
  setup: ["Setup", "Local Setup"],
};

const WORKFLOW_STEPS = [
  { page: "templates", title: "1) Pick a show world", hint: "Choose a starting style, tone, and premise." },
  { page: "bible", title: "2) Write the bible", hint: "Set core rule and recurring premise." },
  { page: "characters", title: "3) Add cast", hint: "Give people names and personality lines." },
  { page: "locations", title: "4) Add places and props", hint: "Your room gets room rules, textures, and hooks." },
  { page: "rooms", title: "5) Arrange the room map", hint: "Move cast, props, jokes, and memory into rooms." },
  { page: "memory", title: "6) Review canon memory", hint: "Memory only changes when you save a scene as canon." },
  { page: "jokes", title: "7) Add jokes and rules", hint: "Load recurring material and relationships." },
  { page: "sparks", title: "8) Choose scene sparks", hint: "Describe a weird scene or pick 1-3 sparks." },
  { page: "generate", title: "9) Generate skit", hint: "Set room, cast size, and click generate." },
];

const PROMPT_EXAMPLES = [
  {
    label: "Saucer + tape",
    prompt: "A flying saucer beams up the landlord behind police tape while two people hold hands.",
  },
  {
    label: "Awkward romance",
    prompt: "Two rivals accidentally hold hands during a fake romantic plan and everyone starts voting on it.",
  },
  {
    label: "Missing prop",
    prompt: "The good mug goes missing and the whole room treats the sofa like a crime scene.",
  },
  {
    label: "Guest panic",
    prompt: "A surprise inspector arrives while everyone hides a terrible plan under a handwritten note.",
  },
];

const DEMO_TEMPLATE_ID = "shared_house";
const DEMO_PROMPT = PROMPT_EXAMPLES[0].prompt;
const DEMO_OPTIONS = {
  seed: 20260627,
  mode: "Random",
  cast_size: 4,
  weirdness: 72,
};

const PAGE_GUIDE_NOTES = {
  start: {
    title: "First thing first",
    text: "Pick a world, fill the Bible, set cast and places, then generate when it turns green.",
  },
  templates: {
    title: "Template = your launch point",
    text: "This sets tone, style, and premise. Start here and change details later.",
  },
  bible: {
    title: "Show spine",
    text: "Keep the premise simple and clear. A strong core gives every scene a direction.",
  },
  characters: {
    title: "People drive scenes",
    text: "Short, specific wants and flaws usually create the best chaos.",
  },
  locations: {
    title: "Spaces create stakes",
    text: "One memorable room + one prop is enough to give scenes an anchor.",
  },
  rooms: {
    title: "Rooms remember",
    text: "Pick where people and props currently are. Generate in a room when you want the scene anchored.",
  },
  memory: {
    title: "Canon is deliberate",
    text: "Generate scenes freely. Only press Save This As Canon when a scene should become memory.",
  },
  jokes: {
    title: "Recurring ingredients",
    text: "Short jokes and clear relationships make scenes read like improv with structure.",
  },
  sparks: {
    title: "Scene steering",
    text: "Describe a weird scene or pick up to three sparks when you want a strong direction.",
  },
  generate: {
    title: "Generate with intent",
    text: "Tune the controls, optionally describe a scene, then press Generate Skit.",
  },
  tester: {
    title: "Phone-call proof",
    text: "Run the same generate, canon, memory, export, and feedback path a tester should understand.",
  },
  library: {
    title: "Saved moments",
    text: "Re-open favourites to reuse or share your best scenes quickly.",
  },
  setup: {
    title: "Local support",
    text: "Use this page if you want to open your export folder or inspect data storage.",
  },
  guide: {
    title: "Your onboarding flow",
    text: "Walk one step at a time. Green means ready, amber means mostly ready, red means blocked.",
  },
};

const state = {
  show: null,
  readiness: null,
  doctor: null,
  templates: [],
  sparks: [],
  selectedSparks: [],
  selectedRoomId: "",
  roomsDirty: false,
  scenePrompt: "",
  promptAnalysis: null,
  favourites: [],
  currentEpisode: null,
  testerStartedAt: null,
  testerExportedAt: null,
  testerCopiedFeedbackAt: null,
  page: pageFromPath(location.pathname),
};

function el(id) {
  return document.getElementById(id);
}

function pageFromPath(path) {
  const page = String(path || "/start").replace("/", "") || "start";
  return PAGES[page] ? page : "start";
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.error || `${APP_NAME} request failed`);
  }
  return data;
}

async function loadApp() {
  const [stateData, favouritesData, doctorData, templatesData, sparksData] = await Promise.all([
    api("/api/state"),
    api("/api/favourites"),
    api("/api/doctor"),
    api("/api/templates"),
    api("/api/sparks"),
  ]);
  state.show = stateData.state;
  state.readiness = stateData.readiness;
  state.favourites = favouritesData.favourites;
  state.doctor = doctorData;
  state.templates = templatesData.templates;
  state.sparks = sparksData.sparks;
  ensureSelectedRoom();
  if (!state.show.template_selected && state.page === "start") {
    state.page = "guide";
    history.replaceState({}, "", "/guide");
  }
  render();
}

function navigate(page, replace = false) {
  state.page = PAGES[page] ? page : "start";
  const url = `/${state.page}`;
  if (replace) {
    history.replaceState({}, "", url);
  } else {
    history.pushState({}, "", url);
  }
  render();
  focusPageTop();
}

function render() {
  if (!state.show || !state.readiness) {
    el("pageRoot").innerHTML = `<section class="panel"><h2>Loading ${APP_NAME}</h2></section>`;
    return;
  }
  const [step, title] = PAGES[state.page];
  document.body.dataset.page = state.page;
  document.body.dataset.mood = pageMood(state.page);
  el("pageStep").textContent = step;
  el("pageTitle").textContent = title;
  el("doctorStatus").textContent = `Local only - v${state.doctor.version}`;
  document.querySelectorAll("[data-page]").forEach((node) => {
    node.classList.toggle("active", node.dataset.page === state.page);
  });
  renderNavigationStatus();
  renderMobileNavigation();
  const sideStatus = el("sideStatus");
  const sidePrefix = state.readiness.next_optional ? "Optional" : labelStatus(state.readiness.overall);
  sideStatus.innerHTML = `${dot(state.readiness.overall)}<span>${escapeHtml(sidePrefix)} - ${escapeHtml(state.readiness.next_action)}</span>`;
  renderCoachRow();

  if (state.page === "start") renderStart();
  if (state.page === "templates") renderTemplates();
  if (state.page === "guide") renderGuide();
  if (state.page === "bible") renderBible();
  if (state.page === "characters") renderCharacters();
  if (state.page === "locations") renderLocations();
  if (state.page === "rooms") renderRooms();
  if (state.page === "memory") renderMemory();
  if (state.page === "jokes") renderJokes();
  if (state.page === "sparks") renderSparks();
  if (state.page === "generate") renderGenerate();
  if (state.page === "tester") renderTester();
  if (state.page === "library") renderLibrary();
  if (state.page === "setup") renderSetup();
}

function pageMood(page) {
  if (page === "sparks") return "sparks";
  if (page === "generate") return "generate";
  if (page === "library") return "library";
  if (page === "setup") return "library";
  return "guide";
}

function renderGuide() {
  const readinessLabel = `${state.readiness.next_action}`;
  const firstRun = !state.show.template_selected;
  el("pageRoot").innerHTML = `
    <section class="panel">
      <h2>Build your first skit in 9 quick steps</h2>
      ${firstRun ? renderFirstRunCard() : ""}
      ${renderPageGuide("guide")}
      <p class="helper-text">Use one page at a time. Complete each step, then move to the next.</p>
      <div class="demo-callout">
        <strong>Want the fast path?</strong>
        <p>Generate one ready-made scene first, then edit the show once you have seen the shape.</p>
        <div class="action-row compact">
          <button class="primary" id="guideDemoButton">Show Me A Funny One</button>
        </div>
        <p class="message" id="guideMessage"></p>
      </div>
      <div class="guide-track guide-track-block">${renderGuideTrack({includeCurrent: true})}</div>
      <p class="helper-text">Ready check: ${escapeHtml(readinessLabel)}</p>
    </section>
  `;
  el("guideDemoButton").addEventListener("click", () => runDemoMode("guideMessage"));
  const firstRunTemplateButton = el("firstRunTemplateButton");
  if (firstRunTemplateButton) {
    firstRunTemplateButton.addEventListener("click", () => navigate("templates"));
  }
  const firstRunDemoButton = el("firstRunDemoButton");
  if (firstRunDemoButton) {
    firstRunDemoButton.addEventListener("click", () => runDemoMode("guideMessage"));
  }
  setGuidePageButtons();
}

function renderCoachRow() {
  if (!state.readiness) {
    return;
  }
  const row = el("coachRow");
  const light = el("coachLight");
  const text = el("coachText");
  const button = el("coachButton");
  const overall = String(state.readiness.overall || "red");
  const nextAction = String(state.readiness.next_action || "Continue");
  const nextPage = state.readiness.next_page || "start";
  const nextPrefix = state.readiness.next_optional ? "Optional" : labelStatus(overall);

  row.classList.remove("red", "amber", "green");
  light.classList.remove("red", "amber", "green");
  row.classList.add(overall);
  light.classList.add(overall);

  text.textContent = `${nextPrefix}: ${nextAction}.`;
  if (nextPage && nextPage !== state.page && PAGES[nextPage]) {
    button.textContent = state.readiness.next_optional ? `Open ${PAGES[nextPage][0]}` : `Go to ${PAGES[nextPage][0]}`;
    button.hidden = false;
    button.onclick = () => navigate(nextPage);
  } else {
    button.hidden = true;
  }
}

function renderNavigationStatus() {
  const nextPage = state.readiness?.next_page || "";
  document.querySelectorAll(".side-nav nav a[data-page]").forEach((link) => {
    const page = link.dataset.page || "start";
    const label = PAGES[page]?.[0] || page;
    const status = navPageStatus(page);
    const isNext = page === nextPage;
    const nextLabel = state.readiness?.next_optional ? "Optional" : "Next";
    link.dataset.status = status;
    link.classList.toggle("next", isNext);
    link.setAttribute("aria-label", `${label}: ${labelStatus(status)}${isNext ? `, ${nextLabel.toLowerCase()} step` : ""}`);
    link.innerHTML = `
      <span class="nav-link-main">
        <span class="nav-status-dot ${escapeAttr(status)}"></span>
        <span>${escapeHtml(label)}</span>
      </span>
      ${isNext ? `<small>${escapeHtml(nextLabel)}</small>` : ""}
    `;
  });
}

function renderMobileNavigation() {
  const panel = el("mobileNavPanel");
  if (!panel || !state.readiness) {
    return;
  }
  const nextPage = state.readiness.next_page || "generate";
  const nextLabel = PAGES[nextPage]?.[0] || "Next";
  const nextPrefix = state.readiness.next_optional ? "Optional" : "Next";
  const pageOptions = Object.entries(PAGES).map(([page, labels]) => {
    const status = labelStatus(navPageStatus(page));
    return `<option value="${escapeAttr(page)}" ${page === state.page ? "selected" : ""}>${escapeHtml(labels[0])} - ${escapeHtml(status)}</option>`;
  }).join("");
  panel.innerHTML = `
    <label class="mobile-page-menu">
      <span>Page</span>
      <select id="mobilePageSelect">${pageOptions}</select>
    </label>
    <button class="mobile-next-button" id="mobileNextButton" ${nextPage === state.page ? "hidden" : ""}>
      ${dot(navPageStatus(nextPage))}
      <span>${escapeHtml(nextPrefix)}: ${escapeHtml(nextLabel)}</span>
    </button>
  `;
  el("mobilePageSelect").addEventListener("change", (event) => navigate(event.target.value));
  const nextButton = el("mobileNextButton");
  if (nextButton && nextPage !== state.page) {
    nextButton.addEventListener("click", () => navigate(nextPage));
  }
}

function navPageStatus(page) {
  if (page === "start" || page === "guide") {
    return state.readiness?.overall || "red";
  }
  if (page === "library") {
    return state.favourites.length ? "green" : "amber";
  }
  if (page === "tester") {
    return state.currentEpisode ? "green" : "amber";
  }
  if (page === "setup") {
    return "green";
  }
  return workflowStepStatus(page);
}

function renderFirstRunCard() {
  return `
    <section class="first-run-card" aria-label="First run steps">
      <div>
        <h3>First run: get a laugh before editing</h3>
        <ol>
          <li>Pick a world, or let Demo Mode load one for you.</li>
          <li>Generate one skit so you can see the shape.</li>
          <li>Edit cast, places, jokes, and sparks after that.</li>
        </ol>
      </div>
      <div class="action-row compact">
        <button class="primary" id="firstRunDemoButton">Show Me A Funny One</button>
        <button id="firstRunTemplateButton">Pick A World</button>
      </div>
    </section>
  `;
}

function setGuidePageButtons() {
  document.querySelectorAll("[data-guide-page]").forEach((button) => {
    const target = button.dataset.guidePage;
    button.addEventListener("click", () => navigate(target));
  });
}

function renderGuideTrack({ includeCurrent = false, fromPage = null, maxSteps = 0 } = {}) {
  const nextPage = state.readiness.next_page || "start";
  const nextLabel = state.readiness.next_optional ? "optional" : "next";
  const startIndex = workflowStartIndex(fromPage);
  const stepCards = [];
  for (const step of WORKFLOW_STEPS.slice(startIndex)) {
    const status = workflowStepStatus(step.page);
    const isCurrent = state.page === step.page;
    const isNext = step.page === nextPage;
    const disabled = isNext ? false : step.page === "generate" && status !== "green";
    const buttonText = step.page === "generate" ? "Open Generator" : `Go to ${PAGES[step.page][0]}`;
    const buttonClass = status === "green" ? "secondary-button" : "primary";
    const statusText = `${labelStatus(status)}${isNext ? ` - ${nextLabel}` : ""}`;
    const buttonMarkup = isCurrent
      ? `<span class="guide-step-status">Current page</span>`
      : `<button class="${buttonClass}" data-guide-page="${escapeAttr(step.page)}" ${disabled ? "disabled" : ""}>${buttonText}</button>`;

    if (!includeCurrent && isCurrent) {
      continue;
    }

    stepCards.push(`
      <article class="guide-step ${status} ${isCurrent ? "current" : ""} ${isNext ? "next" : ""}">
        <header class="guide-step-head">
          ${dot(status)}
          <div>
            <strong>${escapeHtml(step.title)}</strong>
            <small>${escapeHtml(step.hint)}</small>
          </div>
        </header>
        <div class="guide-step-note">
          <span>${escapeHtml(statusText)}</span>
          ${buttonMarkup}
        </div>
      </article>
    `);
    if (maxSteps && stepCards.length >= maxSteps) {
      break;
    }
  }
  return `<div class="guide-track">${stepCards.join("")}</div>`;
}

function workflowStartIndex(fromPage) {
  if (!fromPage) {
    return 0;
  }
  const targetIndex = WORKFLOW_STEPS.findIndex((step) => step.page === fromPage);
  return targetIndex >= 0 ? targetIndex : 0;
}

function workflowStepStatus(page) {
  if (page === "generate") {
    return state.readiness?.can_generate ? "green" : "amber";
  }
  if (!state.readiness?.pages) {
    return "red";
  }
  if (page === "sparks") {
    return "green";
  }
  if (page === "rooms") {
    return state.readiness.pages.rooms || "amber";
  }
  if (page === "memory") {
    return state.readiness.pages.memory || "amber";
  }
  return state.readiness.pages[page] || "red";
}

function renderStart() {
  const canGenerate = canGenerateNow();
  const nextPageHint = state.readiness?.next_action || "Complete your setup and return here";
  el("pageRoot").innerHTML = `
    <div class="page-grid">
      <section class="panel">
        <h2>${escapeHtml(state.show.show_name)}</h2>
        ${renderPageGuide("start")}
        <p>${escapeHtml(state.show.recurring_premise)}</p>
        ${renderReadiness()}
        <div class="action-row">
          <button class="primary" id="startDemoButton">Show Me A Funny One</button>
          <button class="primary" id="startGenerateButton" ${canGenerate ? "" : "disabled"}>Generate Skit</button>
          <button id="startTesterButton">Start Tester Run</button>
        </div>
        <p class="helper-text" id="startMessage">${canGenerate ? "When you are ready, generate your first skit." : `${escapeHtml(nextPageHint)}.`}</p>
      </section>
      <aside class="panel flat">
        <h3>Show Snapshot</h3>
        <div class="pill-row">
          <span class="pill">${escapeHtml(state.show.sitcom_type)}</span>
          <span class="pill">${escapeHtml(state.show.tone)}</span>
          <span class="pill">${state.readiness.counts.characters} cast</span>
          <span class="pill">${state.readiness.counts.jokes} jokes</span>
        </div>
        <p class="next-action"><strong>${state.readiness.next_optional ? "Optional" : "Next"}</strong>${escapeHtml(state.readiness.next_action)}</p>
        <div class="guide-track-mini">
          ${renderGuideTrack({
            includeCurrent: false,
            fromPage: state.readiness.next_page || "templates",
            maxSteps: 3,
          })}
        </div>
      </aside>
    </div>
  `;
  el("startDemoButton").addEventListener("click", () => runDemoMode("startMessage"));
  const startGenerateButton = el("startGenerateButton");
  if (canGenerate) {
    startGenerateButton.addEventListener("click", () => generateEpisode(false));
  }
  el("startTesterButton").addEventListener("click", startTesterRun);
  setGuidePageButtons();
}

function renderTemplates() {
  const cards = state.templates.map((template) => `
    <article class="template-card ${state.show.template_id === template.id ? "active" : ""}">
      <div>
        <h3>${escapeHtml(template.name)}</h3>
        <p>${escapeHtml(template.summary)}</p>
        <div class="pill-row">
          <span class="pill">${escapeHtml(template.type)}</span>
          <span class="pill">${escapeHtml(template.tone)}</span>
        </div>
      </div>
      <button class="primary" data-template-id="${escapeAttr(template.id)}">Use This</button>
    </article>
  `).join("");
  el("pageRoot").innerHTML = `
    <section class="panel">
      <h2>Pick a Starting World</h2>
      ${renderPageGuide("templates")}
      <p>Choose one and start generating straight away. You can edit every part later.</p>
      <div class="template-grid">${cards}</div>
      <section class="world-pack-panel">
        <div>
          <h3>World Packs</h3>
          <p>Export this show as a shareable JSON world, or paste a world pack here and apply it locally.</p>
        </div>
        <div class="action-row compact">
          <button id="exportWorldPackButton">Export Current World</button>
          <button id="openWorldExportsButton">Open Exports Folder</button>
        </div>
        <label class="field">Import World JSON
          <textarea id="worldPackInput" placeholder='Paste a SkitBox world pack JSON here. It can be a full pack with "state", or just the show state.'></textarea>
        </label>
        <div class="action-row compact">
          <button class="primary" id="importWorldPackButton">Apply World Pack</button>
        </div>
      </section>
      <p class="helper-text" id="templatesMessage"></p>
    </section>
  `;
  document.querySelectorAll("[data-template-id]").forEach((button) => {
    button.addEventListener("click", () => applyTemplate(button.dataset.templateId));
  });
  el("exportWorldPackButton").addEventListener("click", () => exportWorldPack("templatesMessage"));
  el("openWorldExportsButton").addEventListener("click", () => openExports("templatesMessage"));
  el("importWorldPackButton").addEventListener("click", () => importWorldPack("templatesMessage"));
}

function renderBible() {
  el("pageRoot").innerHTML = `
    <section class="panel">
      <h2>Show Bible</h2>
      ${renderPageGuide("bible")}
      <div class="form-grid">
        ${field("Show Name", "showName", state.show.show_name)}
        ${selectField("Sitcom Type", "sitcomType", state.show.sitcom_type, ["House", "Office", "Pub", "School", "Family", "Spaceship", "Custom"])}
        ${field("Tone", "tone", state.show.tone)}
        ${textareaField("Core Rule", "coreRule", state.show.core_rule)}
        ${textareaField("Recurring Premise", "recurringPremise", state.show.recurring_premise)}
      </div>
      <div class="action-row">
        <button class="primary" id="saveBibleButton">Save Bible</button>
      </div>
      <p class="helper-text" id="bibleMessage"></p>
    </section>
  `;
  el("saveBibleButton").addEventListener("click", saveBible);
}

function renderCharacters() {
  const text = state.show.characters.map((item) => [
    item.name,
    item.role,
    item.want,
    item.flaw,
    item.phrase,
    item.pressure,
  ].map(clean).join(" | ")).join("\n");
  el("pageRoot").innerHTML = `
    <div class="editor-layout">
      <section class="panel editor-panel">
        <h2>Characters ${state.readiness.counts.characters}/${state.readiness.targets.characters}</h2>
        ${renderPageGuide("characters")}
        <textarea id="charactersText">${escapeHtml(text)}</textarea>
        <div class="action-row">
          <button class="primary" id="saveCharactersButton">Save Characters</button>
        </div>
        <p class="helper-text" id="charactersMessage"></p>
      </section>
      <aside class="format-card">
        <strong>${labelStatus(state.readiness.pages.characters)}</strong>
        <code>Name | role | want | flaw | catchphrase | pressure point</code>
      </aside>
    </div>
  `;
  el("saveCharactersButton").addEventListener("click", saveCharacters);
}

function renderLocations() {
  const locations = state.show.locations.map((item) => [item.name, item.texture, item.rule].map(clean).join(" | ")).join("\n");
  const props = state.show.props.map((item) => [item.name, item.joke].map(clean).join(" | ")).join("\n");
  el("pageRoot").innerHTML = `
    <div class="editor-layout">
      <section class="panel editor-panel">
        <h2>Places & Props</h2>
        ${renderPageGuide("locations")}
        <label class="field">Locations<textarea id="locationsText">${escapeHtml(locations)}</textarea></label>
        <label class="field">Props<textarea id="propsText">${escapeHtml(props)}</textarea></label>
        <div class="action-row">
          <button class="primary" id="saveLocationsButton">Save Places & Props</button>
        </div>
        <p class="helper-text" id="locationsMessage"></p>
      </section>
      <aside class="format-card">
        <strong>${labelStatus(state.readiness.pages.locations)}</strong>
        <code>Location | texture | room rule

Prop | running joke</code>
      </aside>
    </div>
  `;
  el("saveLocationsButton").addEventListener("click", saveLocations);
}

function renderRooms() {
  ensureSelectedRoom();
  const rooms = roomList();
  const active = activeRoom();
  const roomCards = rooms.map((room) => `
    <button class="room-card ${room.id === state.selectedRoomId ? "active" : ""}" data-room-id="${escapeAttr(room.id)}">
      <span class="room-card-name">${escapeHtml(room.name)}</span>
      <span>${escapeHtml(room.mood || "ready")}</span>
      <small>${escapeHtml([...(room.cast || []), ...(room.props || [])].slice(0, 4).join(" + ") || "Empty room")}</small>
    </button>
  `).join("");
  el("pageRoot").innerHTML = `
    <div class="page-grid room-page">
      <section class="panel">
        <h2>Room Map</h2>
        ${renderPageGuide("rooms")}
        <p>Rooms are scene anchors. Move cast and props into one room, then generate there when the traffic light feels right.</p>
        <div class="room-save-reminder ${state.roomsDirty ? "dirty" : "saved"}">
          ${state.roomsDirty ? "Unsaved room changes. Press Save Room Map, or Generate Scene In This Room to save and use them." : "Room map saved. Pick a room, adjust it, then generate there when it feels alive."}
        </div>
        <div class="room-card-grid">${roomCards}</div>
        ${active ? `
          <section class="room-editor" aria-label="Selected room editor">
            <div>
              <h3>${escapeHtml(active.name)}</h3>
              <p>${escapeHtml(active.description || active.location || "A room waiting for a bit.")}</p>
            </div>
            <div class="form-grid">
              ${field("Mood", "roomMoodInput", active.mood || "ready for trouble")}
              ${field("Room Rule", "roomRuleInput", active.rule || "")}
            </div>
            ${textareaField("Room Memory", "roomMemoryInput", active.memory || "")}
            <div class="room-move-grid">
              ${renderRoomMoveControl("cast", "Move Cast", "roomCastSelect", "moveCastButton", (state.show.characters || []).map((item) => item.name))}
              ${renderRoomMoveControl("props", "Move Prop", "roomPropSelect", "movePropButton", (state.show.props || []).map((item) => item.name))}
              ${renderRoomMoveControl("jokes", "Move Joke", "roomJokeSelect", "moveJokeButton", (state.show.jokes || []).map((item) => item.name))}
            </div>
            <div class="room-contents">
              ${renderRoomChips("cast", "Cast", active.cast || [])}
              ${renderRoomChips("props", "Props", active.props || [])}
              ${renderRoomChips("jokes", "Jokes", active.jokes || [])}
            </div>
            <div class="action-row">
              <button class="primary" id="generateRoomButton">Generate Scene In This Room</button>
              <button id="saveRoomsButton">Save Room Map</button>
            </div>
            <p class="helper-text" id="roomsMessage"></p>
          </section>
        ` : `<div class="empty-state"><strong>No rooms yet.</strong><p>Add locations first, then save to build a room map.</p></div>`}
      </section>
      <aside class="panel flat">
        <h3>Room Readiness</h3>
        ${renderReadiness()}
        <p class="next-action"><strong>Selected Room</strong>${escapeHtml(active?.name || "No room selected")}</p>
      </aside>
    </div>
  `;
  document.querySelectorAll("[data-room-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedRoomId = button.dataset.roomId || "";
      renderRooms();
    });
  });
  if (!active) {
    return;
  }
  el("roomMoodInput").addEventListener("input", () => {
    active.mood = el("roomMoodInput").value.trim();
    markRoomsDirty("Mood changed. Save the room map before you leave this page.");
  });
  el("roomRuleInput").addEventListener("input", () => {
    active.rule = el("roomRuleInput").value.trim();
    markRoomsDirty("Rule changed. Save the room map before you leave this page.");
  });
  el("roomMemoryInput").addEventListener("input", () => {
    active.memory = el("roomMemoryInput").value.trim();
    markRoomsDirty("Memory changed. Save the room map before you leave this page.");
  });
  el("moveCastButton").addEventListener("click", () => moveRoomItem("cast", el("roomCastSelect").value));
  el("movePropButton").addEventListener("click", () => moveRoomItem("props", el("roomPropSelect").value));
  el("moveJokeButton").addEventListener("click", () => moveRoomItem("jokes", el("roomJokeSelect").value));
  document.querySelectorAll("[data-remove-room-item]").forEach((button) => {
    button.addEventListener("click", () => removeRoomItem(button.dataset.kind, button.dataset.removeRoomItem));
  });
  el("saveRoomsButton").addEventListener("click", () => saveRooms());
  el("generateRoomButton").addEventListener("click", async () => {
    await saveRooms("Room map saved. Generating from this room...");
    await generateEpisode(false);
  });
}

function renderMemory() {
  const characterCards = memoryCharacterList().map((item) => `
    <article class="memory-card">
      <div class="memory-card-head">
        <strong>${escapeHtml(item.name)}</strong>
        <span>${escapeHtml(item.mood || "ready")}</span>
      </div>
      <p><b>Pressure:</b> ${escapeHtml(item.pressure || "being noticed")}</p>
      <p><b>Last canon:</b> ${escapeHtml(item.last_incident || "Nothing saved yet.")}</p>
      <small>${Number(item.canon_count || 0)} canon save${Number(item.canon_count || 0) === 1 ? "" : "s"}</small>
    </article>
  `).join("");
  const historyCards = memoryRoomHistoryList().map((room) => `
    <article class="memory-card room-memory-card">
      <div class="memory-card-head">
        <strong>${escapeHtml(room.room_name)}</strong>
        <span>${room.incidents.length ? `${room.incidents.length} saved` : "empty"}</span>
      </div>
      ${renderIncidentList(room.incidents)}
      <button class="secondary-button" data-memory-room="${escapeAttr(room.room_id)}">Generate In This Room</button>
    </article>
  `).join("");
  const hasEpisode = Boolean(state.currentEpisode && state.currentEpisode.script);
  const memoryCount = Number(state.readiness.counts.memory || 0);
  el("pageRoot").innerHTML = `
    <div class="page-grid">
      <section class="panel">
        <h2>Canon Memory</h2>
        ${renderPageGuide("memory")}
        <p>Memory is manual. Generate as many scenes as you want; only the scenes you save as canon affect future scenes.</p>
        <div class="memory-save-reminder ${memoryCount ? "saved" : "fresh"}">
          ${memoryCount ? `${memoryCount} saved incident${memoryCount === 1 ? "" : "s"} can now influence room callbacks and character pressure.` : "No canon saved yet. Generate a keeper, then press Save This As Canon."}
        </div>
        <div class="action-row">
          <button class="primary" id="memoryCanonButton" ${hasEpisode ? "" : "disabled"}>Save Current Scene As Canon</button>
          <button class="danger" id="resetMemoryButton">Reset Canon Memory</button>
        </div>
        <p class="message" id="memoryMessage"></p>
        <h3>Character Memory</h3>
        <div class="memory-grid">${characterCards || `<div class="empty-state"><strong>No cast yet.</strong><p>Add characters first.</p></div>`}</div>
      </section>
      <aside class="panel flat">
        <h3>Room History</h3>
        <p class="helper-text">Newest saved incidents appear first. The engine reads these as sitcom callbacks.</p>
        <div class="memory-stack">${historyCards || `<div class="empty-state"><strong>No rooms yet.</strong><p>Add locations to make rooms.</p></div>`}</div>
      </aside>
    </div>
  `;
  el("memoryCanonButton").addEventListener("click", () => saveCanon("memoryMessage"));
  el("resetMemoryButton").addEventListener("click", resetMemory);
  document.querySelectorAll("[data-memory-room]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedRoomId = button.dataset.memoryRoom || "";
      navigate("generate");
    });
  });
}

function renderJokes() {
  const jokes = state.show.jokes.map((item) => [item.name, item.text].map(clean).join(" | ")).join("\n");
  const rules = state.show.rules.map((item) => [item.name, item.text].map(clean).join(" | ")).join("\n");
  const relationships = state.show.relationships.map((item) => [item.from, item.to, item.dynamic].map(clean).join(" | ")).join("\n");
  const premises = state.show.premises.map((item) => [item.title, item.spark].map(clean).join(" | ")).join("\n");
  el("pageRoot").innerHTML = `
    <div class="editor-layout">
      <section class="panel editor-panel">
        <h2>Jokes, Rules & Premises</h2>
        ${renderPageGuide("jokes")}
        <label class="field">Running Jokes<textarea id="jokesText">${escapeHtml(jokes)}</textarea></label>
        <label class="field">Rules<textarea id="rulesText">${escapeHtml(rules)}</textarea></label>
        <label class="field">Relationships<textarea id="relationshipsText">${escapeHtml(relationships)}</textarea></label>
        <label class="field">Premises<textarea id="premisesText">${escapeHtml(premises)}</textarea></label>
        <div class="action-row">
          <button class="primary" id="saveJokesButton">Save Jokes & Rules</button>
        </div>
        <p class="helper-text" id="jokesMessage"></p>
      </section>
      <aside class="format-card">
        <strong>${labelStatus(state.readiness.pages.jokes)}</strong>
        <code>Joke | text
Rule | text
Character | character | dynamic
Premise | spark</code>
      </aside>
    </div>
  `;
  el("saveJokesButton").addEventListener("click", saveJokes);
}

function renderSparks() {
  const sparkCards = state.sparks.map((spark) => `
    <button class="spark-choice ${state.selectedSparks.includes(spark.id) ? "selected" : ""}" data-spark-id="${escapeAttr(spark.id)}">
      <span class="spark-icon ${sparkIconClass(spark.id)}"></span>
      <span><strong>${escapeHtml(spark.name)}</strong><span>${escapeHtml(spark.description)}</span></span>
    </button>
  `).join("");
  const hasSelectedSparks = state.selectedSparks.length > 0;
  el("pageRoot").innerHTML = `
    <div class="page-grid">
      <section class="panel">
        <h2>Pick 1-3 Scene Sparks</h2>
        ${renderPageGuide("sparks")}
        <p>These are not decoration. Selected sparks steer the mode, premise, conflict, and callback.</p>
        <div class="prompt-tool">
          <label class="field">Describe A Weird Scene
            <textarea id="scenePromptInput" placeholder="A flying saucer beams up the landlord behind police tape while two people hold hands.">${escapeHtml(state.scenePrompt)}</textarea>
          </label>
          ${renderPromptExamples()}
          <div class="action-row compact">
            <button id="describePromptButton">Use Description</button>
            <button class="primary" id="promptGenerateButton">Generate From Description</button>
          </div>
          <p class="helper-text" id="promptAnalysisMessage">${escapeHtml(promptAnalysisMessage())}</p>
        </div>
        <div class="spark-choice-grid">${sparkCards}</div>
        <div class="action-row">
          <button class="primary" id="sparkGenerateButton">Generate Skit</button>
          ${hasSelectedSparks ? `<button class="secondary-button" id="clearSparksButton">Clear Sparks</button>` : ""}
        </div>
        <p class="helper-text" id="sparksMessage">${hasSelectedSparks ? `Selected: ${escapeHtml(selectedSparkLabel())}` : "No sparks selected yet."}</p>
      </section>
      <aside class="panel flat">
        <h3>Current Recipe</h3>
        <p class="next-action"><strong>Sparks</strong>${escapeHtml(selectedSparkLabel())}</p>
        <p>Try combinations: UFO + Police Tape, Heart + Bad Plan, Missing Object + Rivalry.</p>
      </aside>
    </div>
  `;
  document.querySelectorAll("[data-spark-id]").forEach((button) => {
    button.addEventListener("click", () => toggleSpark(button.dataset.sparkId));
  });
  el("scenePromptInput").addEventListener("input", () => {
    state.scenePrompt = el("scenePromptInput").value;
    state.promptAnalysis = null;
    setMessage("promptAnalysisMessage", promptAnalysisMessage());
  });
  attachPromptExamples("scenePromptInput", "promptAnalysisMessage", renderSparks);
  el("describePromptButton").addEventListener("click", async () => {
    await describePrompt("scenePromptInput", "promptAnalysisMessage");
    renderSparks();
  });
  el("promptGenerateButton").addEventListener("click", async () => {
    const used = await describePrompt("scenePromptInput", "promptAnalysisMessage");
    if (used) await generateEpisode(false);
  });
  el("sparkGenerateButton").addEventListener("click", () => generateEpisode(false));
  const clearSparksButton = el("clearSparksButton");
  if (clearSparksButton) {
    clearSparksButton.addEventListener("click", () => {
      state.selectedSparks = [];
      state.promptAnalysis = null;
      renderSparks();
    });
  }
}

function renderGenerate() {
  ensureSelectedRoom();
  const episode = state.currentEpisode;
  const hasEpisode = Boolean(episode && episode.script);
  const canGenerate = canGenerateNow();
  el("pageRoot").innerHTML = `
    <div class="page-grid">
      <section class="panel">
        <h2>Generate Skit</h2>
        ${renderPageGuide("generate")}
        ${renderRoomFocusCard()}
        <div class="form-grid">
          ${selectField("Mode", "modeSelect", episode?.mode || "Random", ["Random", "Cold Open", "Bottle Episode", "Misunderstanding", "Rivalry", "Bad Plan", "Guest Star", "Secret Revealed", "Finale Chaos"])}
          ${roomSelectField()}
          ${field("Seed", "seedInput", episode?.seed || "", "auto")}
          <label class="field">Cast Size<input id="castSizeInput" type="number" min="2" max="5" value="${episode?.cast_size || 4}" /></label>
          <label class="field">Weirdness <span id="weirdnessValue">${episode?.weirdness || 58}</span><input id="weirdnessInput" type="range" min="0" max="100" value="${episode?.weirdness || 58}" /></label>
        </div>
        <div class="selected-sparks">
          <strong>Scene Sparks</strong>
          <span>${escapeHtml(selectedSparkLabel())}</span>
          <button id="chooseSparksButton">Choose Sparks</button>
        </div>
        <div class="selected-sparks">
          <strong>Room</strong>
          <span>${escapeHtml(activeRoom()?.name || "No room selected")}</span>
          <button id="chooseRoomsButton">Edit Rooms</button>
        </div>
        <div class="prompt-tool compact-prompt">
          <label class="field">Describe A Weird Scene
            <textarea id="generatePromptInput" placeholder="A chalk outline, a saucer beam, a heart above two people, or whatever your brain throws at it.">${escapeHtml(state.scenePrompt)}</textarea>
          </label>
          ${renderPromptExamples()}
          <div class="action-row compact">
            <button id="interpretPromptButton">Use Description</button>
            <span class="helper-text">${escapeHtml(promptAnalysisMessage())}</span>
          </div>
        </div>
        <div class="action-row">
          <button class="primary" id="generateButton" ${canGenerate ? "" : "disabled"}>Generate Skit</button>
        </div>
        <details class="action-details" id="postGenerateDetails">
          <summary>Skit actions</summary>
          <div class="action-grid" id="postGenerateActions">
            <section class="mini-card">
              <p class="mini-card-title">Save</p>
              <p class="mini-card-copy">Favourite keeps a good skit in the Library. It does not change future scenes.</p>
              <div class="action-row compact">
                <button id="saveFavouriteButton">Save Favourite</button>
              </div>
            </section>
            <section class="mini-card">
              <p class="mini-card-title">Canon</p>
              <p class="mini-card-copy">Canon teaches the selected room and cast to remember this incident later.</p>
              <div class="action-row compact">
                <button id="saveCanonButton">Save This As Canon</button>
                <button id="openMemoryButton">Open Memory</button>
              </div>
            </section>
            <section class="mini-card">
              <p class="mini-card-title">Copy</p>
              <div class="action-row compact">
                <button id="copyEpisodeButton">Copy Skit</button>
                <button id="copyLineButton">Copy Best Line</button>
                <button id="copyShareButton">Copy Share Text</button>
              </div>
            </section>
            <section class="mini-card">
              <p class="mini-card-title">Export</p>
              <div class="action-row compact">
                <button id="exportTxtButton">Export TXT</button>
                <button id="exportHtmlButton">Export HTML</button>
                <button id="exportCardButton">Export Share Card</button>
              </div>
            </section>
            <section class="mini-card">
              <p class="mini-card-title">Replay</p>
              <div class="action-row compact">
                <button id="sameSeedButton">Generate Same Seed</button>
              </div>
            </section>
            <section class="mini-card">
              <p class="mini-card-title">Files</p>
              <div class="action-row compact">
                <button id="openExportsButton">Open Exports Folder</button>
              </div>
            </section>
          </div>
        </details>
        <p class="helper-text">${canGenerate ? "Set the mood and cast, then generate." : "Finish setup before generating a polished skit."}</p>
        <p class="message" id="generateMessage"></p>
        <textarea id="copyFallback" class="copy-fallback" readonly hidden></textarea>
        ${episode ? renderEpisode(episode) : `<div class="empty-state"><strong>Ready to roll.</strong><p>${escapeHtml(state.readiness.next_action)}</p></div>`}
      </section>
      <aside class="panel flat">
        <h3>Why This Happened</h3>
        ${episode ? `<div class="trace-list">${episode.trace_lines.map(escapeHtml).join("<br>")}</div>` : renderReadiness()}
      </aside>
    </div>
  `;
  el("weirdnessInput").addEventListener("input", () => {
    el("weirdnessValue").textContent = el("weirdnessInput").value;
  });
  const roomFocusEditButton = el("roomFocusEditButton");
  if (roomFocusEditButton) {
    roomFocusEditButton.addEventListener("click", () => navigate("rooms"));
  }
  el("chooseSparksButton").addEventListener("click", () => navigate("sparks"));
  el("chooseRoomsButton").addEventListener("click", () => navigate("rooms"));
  el("roomSelect").addEventListener("change", () => {
    state.selectedRoomId = el("roomSelect").value;
    renderGenerate();
  });
  el("generatePromptInput").addEventListener("input", () => {
    state.scenePrompt = el("generatePromptInput").value;
    state.promptAnalysis = null;
  });
  attachPromptExamples("generatePromptInput", "generateMessage", renderGenerate);
  el("interpretPromptButton").addEventListener("click", async () => {
    const used = await describePrompt("generatePromptInput", "generateMessage");
    renderGenerate();
    if (used) setMessage("generateMessage", promptAnalysisMessage());
  });
  el("generateButton").addEventListener("click", () => generateEpisode(false));
  el("sameSeedButton").addEventListener("click", () => generateEpisode(true));
  el("generateButton").disabled = !canGenerate;
  el("postGenerateDetails").hidden = !hasEpisode;
  el("postGenerateDetails").open = hasEpisode;
  el("saveFavouriteButton").hidden = !hasEpisode;
  el("saveCanonButton").hidden = !hasEpisode;
  el("openMemoryButton").hidden = !hasEpisode;
  el("copyEpisodeButton").hidden = !hasEpisode;
  el("copyLineButton").hidden = !hasEpisode;
  el("copyShareButton").hidden = !hasEpisode;
  el("exportTxtButton").hidden = !hasEpisode;
  el("exportHtmlButton").hidden = !hasEpisode;
  el("exportCardButton").hidden = !hasEpisode;
  el("openExportsButton").hidden = !hasEpisode;
  el("sameSeedButton").hidden = !hasEpisode;
  el("saveFavouriteButton").addEventListener("click", saveFavourite);
  el("saveCanonButton").addEventListener("click", () => saveCanon("generateMessage"));
  el("openMemoryButton").addEventListener("click", () => navigate("memory"));
  el("copyEpisodeButton").addEventListener("click", () => copyText(state.currentEpisode?.script || ""));
  el("copyLineButton").addEventListener("click", () => copyText(state.currentEpisode?.share_text || ""));
  el("copyShareButton").addEventListener("click", () => copyText(state.currentEpisode?.share_text || ""));
  el("exportTxtButton").addEventListener("click", () => exportEpisode("txt"));
  el("exportHtmlButton").addEventListener("click", () => exportEpisode("html"));
  el("exportCardButton").addEventListener("click", () => exportEpisode("card"));
  el("openExportsButton").addEventListener("click", () => openExports("generateMessage"));
}

function canGenerateNow() {
  return Boolean(state.readiness && state.readiness.can_generate);
}

function roomList() {
  if (!state.show) return [];
  if (!Array.isArray(state.show.rooms)) {
    state.show.rooms = [];
  }
  return state.show.rooms;
}

function ensureSelectedRoom() {
  const rooms = roomList();
  if (!rooms.length) {
    state.selectedRoomId = "";
    return;
  }
  if (!rooms.some((room) => room.id === state.selectedRoomId)) {
    state.selectedRoomId = rooms[0].id || "";
  }
}

function activeRoom() {
  ensureSelectedRoom();
  return roomList().find((room) => room.id === state.selectedRoomId) || null;
}

function memoryCharacterList() {
  if (Array.isArray(state.show?.character_states) && state.show.character_states.length) {
    return state.show.character_states;
  }
  return (state.show?.characters || []).map((character) => ({
    name: character.name || "Unnamed",
    mood: "ready",
    pressure: character.pressure || "being noticed",
    last_incident: "",
    relationship_nudge: "",
    canon_count: 0,
  }));
}

function memoryRoomHistoryList() {
  if (Array.isArray(state.show?.room_history) && state.show.room_history.length) {
    return state.show.room_history;
  }
  return roomList().map((room) => ({
    room_id: room.id,
    room_name: room.name,
    incidents: [],
  }));
}

function renderIncidentList(incidents) {
  if (!Array.isArray(incidents) || !incidents.length) {
    return `<div class="empty-memory">No saved canon here yet.</div>`;
  }
  return `
    <ol class="incident-list">
      ${incidents.slice(0, 3).map((incident) => `
        <li>
          <strong>${escapeHtml(incident.title || "Untitled Skit")}</strong>
          <span>${escapeHtml(incident.summary || "Saved canon incident.")}</span>
          <small>${escapeHtml(incident.mode || "Scene")} | seed ${escapeHtml(incident.seed || "")}</small>
        </li>
      `).join("")}
    </ol>
  `;
}

function moveRoomItem(kind, value) {
  const active = activeRoom();
  if (!active || !value) return;
  roomList().forEach((room) => {
    room[kind] = Array.isArray(room[kind]) ? room[kind].filter((item) => item !== value) : [];
  });
  active[kind] = Array.isArray(active[kind]) ? active[kind] : [];
  if (!active[kind].includes(value)) {
    active[kind].push(value);
  }
  state.roomsDirty = true;
  renderRooms();
  setMessage("roomsMessage", `${value} moved into ${active.name}. Save the room map, or generate in this room to save and use it now.`);
}

function removeRoomItem(kind, value) {
  const active = activeRoom();
  if (!active || !kind || !value) return;
  active[kind] = Array.isArray(active[kind]) ? active[kind].filter((item) => item !== value) : [];
  state.roomsDirty = true;
  renderRooms();
  setMessage("roomsMessage", `${value} removed from ${active.name}. Save the room map when it looks right.`);
}

function markRoomsDirty(message) {
  state.roomsDirty = true;
  const reminder = document.querySelector(".room-save-reminder");
  if (reminder) {
    reminder.classList.remove("saved");
    reminder.classList.add("dirty");
    reminder.textContent = "Unsaved room changes. Press Save Room Map, or Generate Scene In This Room to save and use them.";
  }
  setMessage("roomsMessage", message || "Room map changed. Save it when it looks right.");
}

function renderLibrary() {
  const items = state.favourites.length
    ? state.favourites.map((item) => `
      <article class="library-item">
        <strong>${escapeHtml(item.title)}</strong>
        <p>${escapeHtml(item.mode || "")} | seed ${escapeHtml(item.seed || "")}</p>
        <div class="button-row">
          <button data-load-fav="${escapeHtml(item.id)}">Open</button>
        </div>
      </article>
    `).join("")
    : `<div class="empty-state"><strong>No favourites yet.</strong><p>Save a skit from Generate.</p></div>`;
  el("pageRoot").innerHTML = `
    <section class="panel">
      <h2>Library</h2>
      ${renderPageGuide("library")}
      <div class="library-list">${items}</div>
    </section>
  `;
  document.querySelectorAll("[data-load-fav]").forEach((button) => {
    button.addEventListener("click", () => {
      const fav = state.favourites.find((item) => item.id === button.dataset.loadFav);
      if (fav) {
        state.currentEpisode = fav.episode;
        navigate("generate");
      }
    });
  });
}

function renderTester() {
  const episode = state.currentEpisode;
  const memoryCount = state.doctor?.doctor?.memory_count || 0;
  const started = state.testerStartedAt ? new Date(state.testerStartedAt).toLocaleTimeString() : "Not started";
  const hasEpisode = Boolean(episode && episode.script);
  const canSaveCanon = hasEpisode;
  const canExport = hasEpisode;
  const exported = Boolean(state.testerExportedAt);
  const copiedFeedback = Boolean(state.testerCopiedFeedbackAt);
  el("pageRoot").innerHTML = `
    <div class="page-grid">
      <section class="panel">
        <h2>Tester Run</h2>
        ${renderPageGuide("tester")}
        <p>This is the short proof path for a stranger: generate, save canon, see memory, export, then copy feedback.</p>
        <div class="tester-status">
          <span class="pill">Started: ${escapeHtml(started)}</span>
          <span class="pill">${hasEpisode ? "Scene ready" : "No scene yet"}</span>
          <span class="pill">${memoryCount} canon incident${memoryCount === 1 ? "" : "s"}</span>
        </div>
        <div class="tester-track">
          ${testerStep("1", "Generate a demo scene", hasEpisode, "A tester should get a skit without editing anything first.", "testerDemoButton", "Generate Demo Scene")}
          ${testerStep("2", "Save the scene as canon", memoryCount > 0, "This is deliberately different from Save Favourite.", "testerCanonButton", "Save Current Scene As Canon", !canSaveCanon)}
          ${testerStep("3", "Check Memory", memoryCount > 0, "The saved incident should appear on the Memory page.", "testerMemoryButton", "Open Memory")}
          ${testerStep("4", "Generate with memory", hasEpisode && memoryCount > 0, "A later scene should mention Previously In This Room.", "testerRememberButton", "Generate Remembered Scene", memoryCount < 1)}
          ${testerStep("5", "Export and share", exported, "Create a local TXT/HTML/share-card export.", "testerExportButton", "Export Share Card", !canExport)}
          ${testerStep("6", "Copy feedback", copiedFeedback, "Paste this summary into GitHub or a message.", "testerCopyButton", "Copy Feedback Summary")}
        </div>
        <p class="message" id="testerMessage"></p>
      </section>
      <aside class="panel flat">
        <h3>Feedback Summary</h3>
        <textarea class="feedback-summary" id="testerFeedbackSummary" readonly>${escapeHtml(testerFeedbackSummary())}</textarea>
        <div class="action-row compact">
          <button id="testerCopySummaryButton">Copy Summary</button>
        </div>
      </aside>
    </div>
  `;
  el("testerDemoButton").addEventListener("click", () => runDemoMode("testerMessage", { returnToPage: "tester" }));
  el("testerCanonButton").addEventListener("click", () => saveCanon("testerMessage"));
  el("testerMemoryButton").addEventListener("click", () => navigate("memory"));
  el("testerRememberButton").addEventListener("click", generateTesterRememberedScene);
  el("testerExportButton").addEventListener("click", () => exportEpisode("card", "testerMessage"));
  el("testerCopyButton").addEventListener("click", () => copyText(testerFeedbackSummary(), "testerMessage"));
  el("testerCopySummaryButton").addEventListener("click", () => copyText(testerFeedbackSummary(), "testerMessage"));
}

function testerStep(number, title, done, text, buttonId, buttonText, disabled = false) {
  return `
    <article class="tester-step ${done ? "done" : ""}">
      <span class="tester-step-number">${escapeHtml(number)}</span>
      <div>
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(text)}</p>
      </div>
      <button id="${escapeAttr(buttonId)}" ${disabled ? "disabled" : ""}>${escapeHtml(buttonText)}</button>
    </article>
  `;
}

function startTesterRun() {
  state.testerStartedAt = Date.now();
  state.testerExportedAt = null;
  state.testerCopiedFeedbackAt = null;
  navigate("tester");
}

function renderSetup() {
  const doctor = state.doctor.doctor;
  el("pageRoot").innerHTML = `
    <div class="page-grid">
      <section class="panel">
        <h2>Local Setup</h2>
        ${renderPageGuide("setup")}
        <p class="data-path">${escapeHtml(doctor.data_dir)}</p>
        <div class="pill-row">
          <span class="pill">${escapeHtml(doctor.storage_mode)}</span>
          <span class="pill">${escapeHtml(state.doctor.python)}</span>
          <span class="pill">${doctor.favourite_count} favourites</span>
        </div>
        <div class="action-row">
          <button id="openSetupExportsButton">Open Exports Folder</button>
          <button id="setupExportWorldButton">Export World Pack</button>
          <button class="danger" id="resetButton">Reset Default Show</button>
        </div>
        <div class="stop-note">
          <strong>Python friction decision</strong>
          <p>For this release, stay with the simple ZIP plus Python launcher. If testers hit Python trouble, the next packaging stage is an EXE build.</p>
        </div>
        <div class="stop-note">
          <strong>When you are finished</strong>
          <p>Close the black launcher window, or double-click <code>STOP_SkitBox_WINDOWS.bat</code> in this folder.</p>
          <p>Developer command: <code>powershell -ExecutionPolicy Bypass -File scripts\\stop_dev_processes.ps1</code></p>
        </div>
        <p class="message" id="setupMessage"></p>
      </section>
      <aside class="panel flat">
        <h3>Readiness</h3>
        ${renderReadiness()}
      </aside>
    </div>
  `;
  el("openSetupExportsButton").addEventListener("click", () => openExports("setupMessage"));
  el("setupExportWorldButton").addEventListener("click", () => exportWorldPack("setupMessage"));
  el("resetButton").addEventListener("click", resetShow);
}

function renderPageGuide(page) {
  const note = PAGE_GUIDE_NOTES[page];
  if (!note) {
    return "";
  }
  const status = navPageStatus(page);
  return `
    <div class="page-coach-card ${escapeAttr(status)}">
      <div class="page-coach-head">
        ${dot(status)}
        <strong>${escapeHtml(note.title)}</strong>
        <span>${escapeHtml(labelStatus(status))}</span>
      </div>
      <p>${escapeHtml(note.text)}</p>
    </div>
  `;
}

function renderPromptExamples() {
  return `
    <div class="prompt-examples" aria-label="Example scene descriptions">
      ${PROMPT_EXAMPLES.map((example) => `
        <button class="prompt-example-button" data-prompt-example="${escapeAttr(example.prompt)}">${escapeHtml(example.label)}</button>
      `).join("")}
    </div>
  `;
}

function renderEpisode(episode) {
  return `
    <section class="result-section">
      <h2 class="episode-title">${escapeHtml(episode.title)}</h2>
      <p class="episode-meta">${escapeHtml(episode.mode)} | seed ${escapeHtml(episode.seed)} | ${escapeHtml(episode.room?.name || "No room")} | ${escapeHtml(episode.setting)}</p>
      <div class="best-line">${escapeHtml(episode.best_line)}</div>
      ${episode.canon_candidate ? `<div class="canon-summary"><strong>Canon candidate</strong><span>${escapeHtml(episode.canon_candidate.summary || "")}</span></div>` : ""}
      <pre class="script-output">${escapeHtml(episode.script)}</pre>
    </section>
  `;
}

function renderReadiness() {
  const readiness = state.readiness;
  return `
    <div class="readiness-board">
      <div class="traffic">
        ${trafficStep("red", "Needs", "Missing basics", readiness.overall)}
        ${trafficStep("amber", "Playable", "Good enough to generate", readiness.overall)}
        ${trafficStep("green", "Ready", "Fuller skit fuel", readiness.overall)}
      </div>
      <div class="meter-grid">
        ${meter("Cast", readiness.counts.characters, readiness.targets.characters)}
        ${meter("Locations", readiness.counts.locations, readiness.targets.locations)}
        ${meter("Props", readiness.counts.props, readiness.targets.props)}
        ${meter("Rooms", readiness.counts.rooms, readiness.targets.rooms)}
        ${meter("Memory", readiness.counts.memory, readiness.targets.memory)}
        ${meter("Jokes", readiness.counts.jokes, readiness.targets.jokes)}
        ${meter("Rules", readiness.counts.rules, readiness.targets.rules)}
        ${meter("Relationships", readiness.counts.relationships, readiness.targets.relationships)}
        ${meter("Premises", readiness.counts.premises, readiness.targets.premises)}
      </div>
    </div>
  `;
}

function trafficStep(status, title, text, active) {
  return `
    <div class="traffic-step ${status === active ? "active" : ""}">
      ${dot(status)}
      <strong>${title}</strong>
      <span>${text}</span>
    </div>
  `;
}

function meter(label, count, target) {
  return `<div class="meter"><strong>${count}/${target}</strong><span>${label}</span></div>`;
}

function field(label, id, value, placeholder = "") {
  return `<label class="field">${label}<input id="${id}" value="${escapeAttr(value)}" placeholder="${escapeAttr(placeholder)}" /></label>`;
}

function textareaField(label, id, value) {
  return `<label class="field">${label}<textarea id="${id}">${escapeHtml(value)}</textarea></label>`;
}

function selectField(label, id, value, options) {
  return `
    <label class="field">${label}
      <select id="${id}">
        ${options.map((option) => `<option ${option === value ? "selected" : ""}>${escapeHtml(option)}</option>`).join("")}
      </select>
    </label>
  `;
}

function roomSelectField() {
  const rooms = roomList();
  return `
    <label class="field">Room
      <select id="roomSelect">
        ${rooms.map((room) => `<option value="${escapeAttr(room.id)}" ${room.id === state.selectedRoomId ? "selected" : ""}>${escapeHtml(room.name)}</option>`).join("")}
      </select>
    </label>
  `;
}

function renderRoomFocusCard() {
  const room = activeRoom();
  if (!room) {
    return `
      <section class="room-focus-card">
        <strong>No room selected</strong>
        <p>Open Rooms to pick where this scene happens.</p>
      </section>
    `;
  }
  const ingredients = [
    ...(room.cast || []).slice(0, 3),
    ...(room.props || []).slice(0, 2),
    ...(room.jokes || []).slice(0, 1),
  ].join(" + ");
  return `
    <section class="room-focus-card">
      <div>
        <span class="mini-card-title">Selected Room</span>
        <strong>${escapeHtml(room.name)}</strong>
        <p>${escapeHtml(room.mood || "ready")} ${ingredients ? `| ${ingredients}` : ""}</p>
      </div>
      <button id="roomFocusEditButton">Edit Room</button>
    </section>
  `;
}

function renderRoomMoveControl(kind, label, selectId, buttonId, options) {
  const uniqueOptions = [...new Set(options.filter(Boolean))];
  return `
    <div class="room-move-control">
      <label class="field">${label}
        <select id="${selectId}">
          ${uniqueOptions.map((option) => `<option value="${escapeAttr(option)}">${escapeHtml(option)}</option>`).join("")}
        </select>
      </label>
      <button id="${buttonId}" data-move-kind="${escapeAttr(kind)}" ${uniqueOptions.length ? "" : "disabled"}>Move Here</button>
    </div>
  `;
}

function renderRoomChips(kind, label, names) {
  const chips = names.length
    ? names.map((name) => `
      <button class="room-chip" data-kind="${escapeAttr(kind)}" data-remove-room-item="${escapeAttr(name)}">
        <span>${escapeHtml(name)}</span>
        <small>Remove</small>
      </button>
    `).join("")
    : `<span class="room-empty-chip">Nothing here yet</span>`;
  return `
    <section class="room-content-block">
      <h4>${escapeHtml(label)}</h4>
      <div class="room-chip-row">${chips}</div>
    </section>
  `;
}

async function saveBible() {
  state.show.show_name = el("showName").value.trim() || "Untitled Sitcom";
  state.show.sitcom_type = el("sitcomType").value;
  state.show.tone = el("tone").value.trim() || "warm chaos";
  state.show.core_rule = el("coreRule").value.trim();
  state.show.recurring_premise = el("recurringPremise").value.trim();
  await saveState("bibleMessage", "Bible saved.");
}

async function saveCharacters() {
  state.show.characters = lines(el("charactersText").value).map((parts) => ({
    name: parts[0] || "Unnamed",
    role: parts[1] || "cast member",
    want: parts[2] || "to get through the scene",
    flaw: parts[3] || "chooses the wrong moment",
    phrase: parts[4] || "Right.",
    pressure: parts[5] || "being noticed",
  }));
  await saveState("charactersMessage", "Characters saved.");
}

async function saveLocations() {
  state.show.locations = lines(el("locationsText").value).map((parts) => ({
    name: parts[0] || "Unnamed Location",
    texture: parts[1] || "a room with timing",
    rule: parts[2] || "small problems get louder here",
  }));
  state.show.props = lines(el("propsText").value).map((parts) => ({
    name: parts[0] || "Unnamed Prop",
    joke: parts[1] || "it becomes important too quickly",
  }));
  await saveState("locationsMessage", "Places and props saved.");
}

async function saveJokes() {
  state.show.jokes = lines(el("jokesText").value).map((parts) => ({
    name: parts[0] || "Unnamed Joke",
    text: parts[1] || "it comes back at the wrong time",
  }));
  state.show.rules = lines(el("rulesText").value).map((parts) => ({
    name: parts[0] || "Unnamed Rule",
    text: parts[1] || "the room takes it seriously",
  }));
  state.show.relationships = lines(el("relationshipsText").value).map((parts) => ({
    from: parts[0] || "Someone",
    to: parts[1] || "Someone Else",
    dynamic: parts[2] || "they know exactly how to annoy each other",
  }));
  state.show.premises = lines(el("premisesText").value).map((parts) => ({
    title: parts[0] || "Untitled Premise",
    spark: parts[1] || "a normal job becomes everyone's problem",
  }));
  await saveState("jokesMessage", "Jokes, rules, relationships, and premises saved.");
}

async function saveRooms(message = "Room map saved.") {
  const active = activeRoom();
  if (active) {
    active.mood = el("roomMoodInput")?.value.trim() || active.mood || "ready";
    active.rule = el("roomRuleInput")?.value.trim() || active.rule || "";
    active.memory = el("roomMemoryInput")?.value.trim() || active.memory || "";
  }
  state.roomsDirty = false;
  await saveState("roomsMessage", message);
}

async function saveState(messageId, message) {
  const data = await api("/api/state", {
    method: "POST",
    body: JSON.stringify({ state: state.show }),
  });
  state.show = data.state;
  state.readiness = data.readiness;
  ensureSelectedRoom();
  render();
  const target = el(messageId);
  if (target) target.textContent = message;
}

async function applyTemplate(templateId) {
  const data = await api("/api/template", {
    method: "POST",
    body: JSON.stringify({ template_id: templateId }),
  });
  state.show = data.state;
  state.readiness = data.readiness;
  state.currentEpisode = null;
  ensureSelectedRoom();
  await refreshDoctor();
  navigate("start", true);
}

async function generateEpisode(sameSeed) {
  const previous = state.currentEpisode;
  const seedValue = sameSeed && previous ? previous.seed : el("seedInput")?.value.trim();
  const promptInput = el("generatePromptInput") || el("scenePromptInput");
  if (promptInput) state.scenePrompt = promptInput.value.trim();
  const payload = {
    mode: el("modeSelect")?.value || "Random",
    seed: seedValue || undefined,
    cast_size: el("castSizeInput")?.value || 4,
    weirdness: el("weirdnessInput")?.value || 58,
    room_id: state.selectedRoomId || undefined,
    sparks: state.selectedSparks,
    prompt: state.scenePrompt || undefined,
  };
  const data = await api("/api/generate", { method: "POST", body: JSON.stringify(payload) });
  state.currentEpisode = data.episode;
  state.selectedRoomId = data.episode.room?.id || state.selectedRoomId;
  state.promptAnalysis = data.episode.prompt_analysis || state.promptAnalysis;
  state.scenePrompt = data.episode.scene_prompt || state.scenePrompt;
  state.readiness = data.readiness;
  state.page = "generate";
  history.replaceState({}, "", "/generate");
  render();
  focusGeneratedEpisode();
}

async function describePrompt(inputId, messageId) {
  const input = el(inputId);
  if (input) state.scenePrompt = input.value.trim();
  if (!state.scenePrompt) {
    state.promptAnalysis = null;
    setMessage(messageId, "Type a scene first.");
    return false;
  }
  const data = await api("/api/describe", {
    method: "POST",
    body: JSON.stringify({ prompt: state.scenePrompt }),
  });
  state.promptAnalysis = data.analysis;
  state.selectedSparks = data.analysis.spark_ids || [];
  setMessage(messageId, promptAnalysisMessage());
  return true;
}

async function runDemoMode(messageId, options = {}) {
  try {
    if (!state.testerStartedAt && options.returnToPage === "tester") {
      state.testerStartedAt = Date.now();
    }
    setMessage(messageId, "Building a demo scene...");
    if (!state.show.template_selected) {
      const templateData = await api("/api/template", {
        method: "POST",
        body: JSON.stringify({ template_id: DEMO_TEMPLATE_ID }),
      });
      state.show = templateData.state;
      state.readiness = templateData.readiness;
      ensureSelectedRoom();
    }

    state.scenePrompt = DEMO_PROMPT;
    const described = await api("/api/describe", {
      method: "POST",
      body: JSON.stringify({ prompt: state.scenePrompt }),
    });
    state.promptAnalysis = described.analysis;
    state.selectedSparks = described.analysis.spark_ids || [];

    const generated = await api("/api/generate", {
      method: "POST",
      body: JSON.stringify({
        ...DEMO_OPTIONS,
        room_id: state.selectedRoomId || undefined,
        prompt: state.scenePrompt,
        sparks: state.selectedSparks,
      }),
    });
    state.currentEpisode = generated.episode;
    state.selectedRoomId = generated.episode.room?.id || state.selectedRoomId;
    state.readiness = generated.readiness;
    state.promptAnalysis = generated.episode.prompt_analysis || state.promptAnalysis;
    state.scenePrompt = generated.episode.scene_prompt || state.scenePrompt;
    const targetPage = options.returnToPage || "generate";
    state.page = targetPage;
    history.replaceState({}, "", `/${targetPage}`);
    render();
    setMessage(targetPage === "tester" ? "testerMessage" : "generateMessage", "Demo scene generated. Change the prompt when you want your own one.");
  } catch (error) {
    setMessage(messageId, error.message || "Demo could not run.");
  }
}

async function generateTesterRememberedScene() {
  if (!state.testerStartedAt) {
    state.testerStartedAt = Date.now();
  }
  const payload = {
    mode: "Random",
    seed: 20260629,
    cast_size: 4,
    weirdness: 72,
    room_id: state.selectedRoomId || undefined,
    prompt: state.scenePrompt || DEMO_PROMPT,
    sparks: state.selectedSparks,
  };
  const data = await api("/api/generate", { method: "POST", body: JSON.stringify(payload) });
  state.currentEpisode = data.episode;
  state.selectedRoomId = data.episode.room?.id || state.selectedRoomId;
  state.promptAnalysis = data.episode.prompt_analysis || state.promptAnalysis;
  state.scenePrompt = data.episode.scene_prompt || state.scenePrompt;
  state.readiness = data.readiness;
  state.page = "tester";
  history.replaceState({}, "", "/tester");
  render();
  setMessage("testerMessage", state.currentEpisode.script.includes("Previously In This Room") ? "Remembered scene generated." : "Scene generated. Save canon first if memory is not visible yet.");
}

function attachPromptExamples(inputId, messageId, afterUse) {
  document.querySelectorAll("[data-prompt-example]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.scenePrompt = button.dataset.promptExample || "";
      const input = el(inputId);
      if (input) {
        input.value = state.scenePrompt;
      }
      await describePrompt(inputId, messageId);
      if (afterUse) afterUse();
    });
  });
}

async function refreshDoctor() {
  const doctorData = await api("/api/doctor");
  state.doctor = doctorData;
}

async function saveFavourite() {
  if (!state.currentEpisode) {
    setMessage("generateMessage", "Generate a skit first.");
    return;
  }
  const data = await api("/api/favourites", {
    method: "POST",
    body: JSON.stringify({ episode: state.currentEpisode }),
  });
  state.favourites = data.favourites;
  setMessage("generateMessage", "Saved to Library.");
}

async function saveCanon(messageId = "generateMessage") {
  if (!state.currentEpisode) {
    setMessage(messageId, "Generate a skit first.");
    return;
  }
  const data = await api("/api/canon", {
    method: "POST",
    body: JSON.stringify({ episode: state.currentEpisode }),
  });
  state.show = data.state;
  state.readiness = data.readiness;
  ensureSelectedRoom();
  await refreshDoctor();
  render();
  setMessage(messageId, `Canon saved: ${data.incident.summary}`);
}

async function resetMemory() {
  const data = await api("/api/memory/reset", { method: "POST", body: JSON.stringify({}) });
  state.show = data.state;
  state.readiness = data.readiness;
  ensureSelectedRoom();
  await refreshDoctor();
  render();
  setMessage("memoryMessage", "Canon memory reset. Rooms, cast, jokes, and favourites are still here.");
}

async function exportEpisode(format, messageId = "generateMessage") {
  if (!state.currentEpisode) {
    setMessage(messageId, "Generate a skit first.");
    return;
  }
  const data = await api("/api/export", {
    method: "POST",
    body: JSON.stringify({ episode: state.currentEpisode, format }),
  });
  if (messageId === "testerMessage" && format === "card") {
    state.testerExportedAt = Date.now();
    if (state.page === "tester") render();
  }
  setMessage(messageId, `Exported ${data.export.format.toUpperCase()}: ${data.export.path}`);
}

async function exportWorldPack(messageId = "templatesMessage") {
  const data = await api("/api/world-pack/export", { method: "POST", body: JSON.stringify({}) });
  setMessage(messageId, `World pack exported: ${data.world_pack.path}`);
}

async function importWorldPack(messageId = "templatesMessage") {
  const input = el("worldPackInput");
  if (!input || !input.value.trim()) {
    setMessage(messageId, "Paste a world pack JSON first.");
    return;
  }
  let payload;
  try {
    payload = JSON.parse(input.value);
  } catch {
    setMessage(messageId, "That does not look like valid JSON.");
    return;
  }
  const data = await api("/api/world-pack/import", {
    method: "POST",
    body: JSON.stringify({ world_pack: payload }),
  });
  state.show = data.state;
  state.readiness = data.readiness;
  state.currentEpisode = null;
  ensureSelectedRoom();
  await refreshDoctor();
  render();
  setMessage(messageId, "World pack applied locally.");
}

async function openExports(messageId = "generateMessage") {
  const data = await api("/api/open-exports", { method: "POST", body: JSON.stringify({}) });
  const message = data.export_folder.opened
    ? `Opened exports: ${data.export_folder.path}`
    : `Exports folder: ${data.export_folder.path}`;
  setMessage(messageId, message);
}

async function resetShow() {
  const data = await api("/api/state", { method: "POST", body: JSON.stringify({ reset: true }) });
  state.show = data.state;
  state.readiness = data.readiness;
  state.currentEpisode = null;
  ensureSelectedRoom();
  state.page = "templates";
  history.replaceState({}, "", "/templates");
  render();
  setMessage("setupMessage", "Default show restored.");
}

function toggleSpark(sparkId) {
  if (!sparkId) return;
  if (state.selectedSparks.includes(sparkId)) {
    state.selectedSparks = state.selectedSparks.filter((id) => id !== sparkId);
  } else if (state.selectedSparks.length < 3) {
    state.selectedSparks = [...state.selectedSparks, sparkId];
  }
  state.promptAnalysis = null;
  renderSparks();
}

function selectedSparkLabel() {
  if (!state.selectedSparks.length) return "No sparks selected";
  return state.selectedSparks
    .map((id) => state.sparks.find((spark) => spark.id === id)?.name || id)
    .join(" + ");
}

function promptAnalysisMessage() {
  const prompt = String(state.scenePrompt || "").trim();
  if (state.promptAnalysis && state.promptAnalysis.summary) {
    return state.promptAnalysis.summary;
  }
  if (prompt) {
    return "Description ready. Use Description to turn it into sparks.";
  }
  return "Try: saucer beam, police tape, chalk outline, heart moment, missing prop, guest, secret, or bad plan.";
}

function sparkIconClass(id) {
  if (id === "ufo_beam") return "ufo-mini";
  if (id === "police_tape") return "mystery-mini";
  if (id === "heart_moment") return "heart-mini";
  if (id === "missing_object") return "object-mini";
  if (id === "guest_arrives") return "guest-mini";
  if (id === "bad_plan") return "plan-mini";
  if (id === "rivalry") return "rivalry-mini";
  return "secret-mini";
}

async function copyText(text, messageId = "generateMessage") {
  if (!text) {
    setMessage(messageId, "Nothing to copy yet.");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    if (messageId === "testerMessage") {
      state.testerCopiedFeedbackAt = Date.now();
      if (state.page === "tester") render();
    }
    setMessage(messageId, "Copied.");
  } catch {
    const fallback = el("copyFallback");
    if (messageId === "testerMessage") {
      state.testerCopiedFeedbackAt = Date.now();
      if (state.page === "tester") render();
    }
    if (fallback) {
      fallback.hidden = false;
      fallback.value = text;
      fallback.focus();
      fallback.select();
      document.execCommand("copy");
      setMessage(messageId, "Copied. If the browser blocked it, the text is selected below.");
    } else {
      setMessage(messageId, "Copy was blocked by the browser. Select the summary text manually.");
    }
  }
}

function testerFeedbackSummary() {
  const episode = state.currentEpisode || {};
  const doctor = state.doctor?.doctor || {};
  const memoryCount = doctor.memory_count || 0;
  const started = state.testerStartedAt ? new Date(state.testerStartedAt).toISOString() : "not started";
  return [
    "SkitBox tester run",
    `Started: ${started}`,
    `Version: ${state.doctor?.version || "unknown"}`,
    `Storage: ${doctor.data_dir || "unknown"}`,
    `Generated scene: ${episode.title || "not yet"}`,
    `Mode/seed: ${episode.mode || "n/a"} / ${episode.seed || "n/a"}`,
    `Room: ${episode.room?.name || "n/a"}`,
    `Canon incidents: ${memoryCount}`,
    `Favourite count: ${doctor.favourite_count || 0}`,
    `Best line: ${episode.best_line || "n/a"}`,
    "Python blocked tester: yes/no",
    "Export made sense: yes/no",
    "Save Favourite vs Save Canon made sense: yes/no",
    "Funniest bit:",
    "Confusing bit:",
  ].join("\n");
}

function lines(text) {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.split("|").map((part) => part.trim()));
}

function setMessage(id, text) {
  const target = el(id);
  if (target) target.textContent = text;
}

function focusPageTop() {
  window.scrollTo({ top: 0, left: 0, behavior: "auto" });
  const root = el("pageRoot");
  if (root) {
    root.focus({ preventScroll: true });
  }
}

function focusGeneratedEpisode() {
  requestAnimationFrame(() => {
    const result = document.querySelector(".result-section");
    if (result) {
      result.scrollIntoView({ block: "start", behavior: "auto" });
      return;
    }
    focusPageTop();
  });
}

function dot(status) {
  return `<span class="status-dot ${escapeHtml(status)}"></span>`;
}

function labelStatus(status) {
  if (status === "green") return "Green";
  if (status === "amber") return "Amber";
  return "Red";
}

function clean(value) {
  return String(value || "").replace(/\|/g, "/");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

document.addEventListener("click", (event) => {
  const link = event.target.closest("[data-link]");
  if (!link) return;
  event.preventDefault();
  navigate(link.dataset.page || pageFromPath(new URL(link.href).pathname));
});

window.addEventListener("popstate", () => {
  state.page = pageFromPath(location.pathname);
  render();
});

loadApp().catch((error) => {
  el("pageRoot").innerHTML = `<section class="panel"><h2>Could not start ${APP_NAME}</h2><p>${escapeHtml(error.message)}</p></section>`;
});
