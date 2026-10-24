document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menuToggle");
  const nav = document.getElementById("mainNav");
  if (menuToggle && nav) {
    menuToggle.addEventListener("click", () => nav.classList.toggle("open"));
  }

  const eligibilityForm = document.getElementById("eligibilityForm");
  const eligibilityResults = document.getElementById("eligibilityResults");
  if (eligibilityForm && eligibilityResults) {
    eligibilityForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = eligibilityForm.querySelector('button[type="submit"]');
      button.disabled = true;
      button.textContent = (JANSEVA_I18N[document.documentElement.dataset.language] || JANSEVA_I18N.en).loading;
      eligibilityResults.textContent = "";
      try {
        const payload = Object.fromEntries(new FormData(eligibilityForm).entries());
        const response = await fetch("/api/eligibility", {
          method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (response.status === 401 && data.login_required) { window.location.href = "/login"; return; }
        if (!response.ok) throw new Error(data.error || "कृपया जानकारी जाँचें।");
        const title = document.createElement("h4");
        title.textContent = (JANSEVA_I18N[document.documentElement.dataset.language] || JANSEVA_I18N.en).suggestions_title;
        eligibilityResults.appendChild(title);
        data.suggestions.forEach(item => {
          const div = document.createElement("div"); div.className = "suggestion";
          const a = document.createElement("a"); a.href = item.url; a.target = "_blank"; a.rel = "noopener noreferrer"; a.textContent = item.title + " ↗";
          const p = document.createElement("p"); p.textContent = item.reason;
          div.append(a,p); eligibilityResults.appendChild(div);
        });
        const note = document.createElement("p"); note.className = "privacy-note"; note.textContent = data.disclaimer; eligibilityResults.appendChild(note);
      } catch (error) {
        eligibilityResults.textContent = error.message || "Server से संपर्क नहीं हो पाया।";
      } finally {
        button.disabled = false; button.innerHTML = 'मेरे सुझाव देखें <span>↗</span>';
      }
    });
  }

  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.getElementById("chatMessages");
  function addMessage(text, type) {
    const div = document.createElement("div"); div.className = "message " + type; div.textContent = text;
    chatMessages.appendChild(div); chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  const chatHistory = [];
  async function askAssistant(message) {
    addMessage(message, "user-message");
    const wait = document.createElement("div"); wait.className = "message bot-message"; wait.textContent = (JANSEVA_I18N[document.documentElement.dataset.language] || JANSEVA_I18N.en).chat_loading; chatMessages.appendChild(wait);
    try {
      const response = await fetch("/api/assistant", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message, language: document.documentElement.dataset.language || "en", history: chatHistory.slice(-10)})});
      const data = await response.json();
      if (response.status === 401 && data.login_required) {
        wait.textContent = data.error || "Please log in to use AI JanSeva.";
        const link = document.createElement("a");
        link.href = "/login";
        link.textContent = " Login";
        link.className = "login-required-link";
        wait.appendChild(link);
      } else {
        wait.textContent = data.answer || data.error || "कोई जवाब उपलब्ध नहीं है।";
        if (response.ok && data.answer) { chatHistory.push({role:"user", text:message}, {role:"model", text:data.answer}); }
      }
    } catch (error) { wait.textContent = (JANSEVA_I18N[document.documentElement.dataset.language] || JANSEVA_I18N.en).chat_error; }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
  if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener("submit", async (event) => {
      event.preventDefault(); const message = chatInput.value.trim(); if (!message) return;
      chatInput.value = ""; await askAssistant(message);
    });
    document.querySelectorAll("[data-prompt]").forEach(button => {
      button.addEventListener("click", () => askAssistant(button.dataset.prompt));
    });
  }
});



/* ===== UI language support (English, Hindi, Bengali, Tamil, Telugu) ===== */
const JANSEVA_I18N = {
  en: {
    problems_eyebrow:'REAL LIFE PROBLEMS',
    problems_title:'One place for everyday help.',
    problems_intro:'Common problems faced by citizens and students in India.',
    problem_scholarships:'Scholarships',
    problem_scholarships_desc:'Understand scholarship options and basic eligibility requirements.',
    problem_documents:'Documents',
    problem_documents_desc:'Get guidance about common documents and citizen services.',
    problem_health:'Healthcare',
    problem_health_desc:'Find information about public healthcare schemes and services.',
    problem_farmers:'Farm Support',
    problem_farmers_desc:'Explore agricultural assistance and farmer-oriented schemes.',
    nav_problems:"Problems",nav_schemes:"Schemes",nav_eligibility:"Eligibility",nav_help:"AI Help",nav_saved:"Saved Schemes",nav_login:"Login",nav_register:"Register",nav_logout:"Logout",nav_greeting:"Welcome",
    footer_tagline:"Government information, made simple.",footer_note:"AI JanSeva is an educational project, not a government website. Verify eligibility, benefits and deadlines on the relevant official portal.",
    hero_eyebrow:"SMART CITIZEN ASSISTANT",hero_title:"Government help,",hero_title_accent:"made simple.",hero_lead:"AI JanSeva helps people understand government schemes, public services and everyday citizen problems in simple language.",
    hero_cta_schemes:"Explore Schemes ↗",hero_cta_eligibility:"Check Eligibility",hero_proof_1:"✓ 40+ scheme and service cards",hero_proof_2:"✓ Official portal links",hero_proof_3:"✓ Multiple languages",
    assistant_name:"JanSeva AI",assistant_subtitle:"Citizen Assistant",hero_chat_user:"I am a student. Are there scholarships?",hero_chat_bot:"You may find suitable scholarship opportunities depending on your state, category, course and family income.",
    stat_categories:"Categories",stat_schemes:"Scheme cards",stat_access:"Website access",trust_label:"INFORMATION CATEGORIES",cat_education:"Education",cat_healthcare:"Healthcare",cat_agriculture:"Agriculture",cat_employment:"Employment",cat_services:"Citizen Services",
    schemes_eyebrow:"GOVERNMENT SCHEMES",schemes_title:"Everything you need,",schemes_title_accent:"in one place.",schemes_intro:"Search schemes, choose a category, and verify the rules on the official website before applying.",
    search_placeholder:"Search schemes, services or keywords...",category_aria:"Choose category",all_categories:"All categories",search_button:"Search",reset_filters:"Reset filters ↗",
    eligibility_eyebrow:"SMART PROFILE",eligibility_title:"Build your citizen",eligibility_title_accent:"profile.",eligibility_intro:"Enter basic information to discover schemes and official links you may want to check. Suggestions are not an official eligibility decision.",
    eligibility_point_1:"✓ Suggested areas to check",eligibility_point_2:"✓ Official links included",eligibility_point_3:"✓ Profile details are not stored",profile_title:"Citizen Information",profile_subtitle:"Enter your basic details",field_age:"Age",field_income:"Annual family income (₹)",field_occupation:"Occupation",field_state:"State",field_category:"Category (optional)",analyze_button:"Analyze Profile ↗",privacy_note:"Your information is used only for this request.",
    help_eyebrow:"JANSEVA HELP",help_title:"Ask a question,",help_title_accent:"get a simple answer.",help_intro:"Ask about schemes, documents, scholarships, healthcare and farmer support. This built-in guide is not connected to a live generative AI model.",
    help_card_title:"Hello! I am JanSeva Help.",help_card_intro:"Ask about government schemes, documents, scholarships, healthcare and farmer support.",prompt_scholarship:"🎓 Scholarships",prompt_documents:"🪪 Documents",prompt_farmers:"🌾 Farmer support",prompt_health:"✚ Healthcare",chat_panel_title:"JanSeva Help",chat_panel_subtitle:"Built-in information guide",chat_welcome:"Hello! What can I help you with today?",chat_placeholder:"Ask about a government service...",chat_disclaimer:"Please verify information on the official government portal.",
    faq_eyebrow:"HELP CENTER",faq_title:"Frequently asked",faq_title_accent:"questions.",faq_intro:"A few important things to know before you begin.",faq1_q:"Is this an official government website?",faq1_a:"No. AI JanSeva is an educational citizen-assistance prototype, not a government department or official portal.",faq2_q:"Does this website confirm my eligibility?",faq2_a:"No. It provides initial suggestions only. Eligibility depends on current scheme rules and your circumstances.",faq3_q:"Can I save my favourite schemes?",faq3_a:"Yes. Register and log in to add schemes to your Saved Schemes list.",faq4_q:"Is AI Help connected to live AI?",faq4_a:"This version uses built-in topic-based guidance. Live AI requires a provider API and secure backend configuration.",faq5_q:"How can I protect my personal information?",faq5_a:"Never share OTPs, passwords, UPI PINs or bank PINs. Use official portals for applications.",
    loading:"Preparing suggestions…",suggestions_title:"Options to check for your profile",chat_loading:"Checking information…",chat_error:"Could not contact the server. Please try again.",no_results:"No schemes found",no_results_help:"Try another keyword or category.",view_all:"View all schemes"
  },
  hi: {
    problems_eyebrow:'रोज़मर्रा की समस्याएँ',
    problems_title:'रोज़मर्रा की मदद, एक ही जगह।',
    problems_intro:'भारत में नागरिकों और छात्रों के सामने आने वाली आम समस्याएँ।',
    problem_scholarships:'छात्रवृत्ति',
    problem_scholarships_desc:'छात्रवृत्ति विकल्पों और बुनियादी पात्रता की जानकारी पाएँ।',
    problem_documents:'दस्तावेज़',
    problem_documents_desc:'ज़रूरी दस्तावेज़ों और नागरिक सेवाओं की जानकारी पाएँ।',
    problem_health:'स्वास्थ्य सेवा',
    problem_health_desc:'सरकारी स्वास्थ्य योजनाओं और सेवाओं की जानकारी पाएँ।',
    problem_farmers:'किसान सहायता',
    problem_farmers_desc:'कृषि सहायता और किसानों के लिए योजनाएँ देखें।',
    nav_problems:"समस्याएँ",nav_schemes:"योजनाएँ",nav_eligibility:"पात्रता",nav_help:"AI सहायता",nav_saved:"सेव की गई योजनाएँ",nav_login:"लॉगिन",nav_register:"रजिस्टर",nav_logout:"लॉगआउट",nav_greeting:"नमस्ते",
    footer_tagline:"सरकारी जानकारी, आसान भाषा में।",footer_note:"AI JanSeva एक शैक्षणिक प्रोजेक्ट है, सरकारी वेबसाइट नहीं। पात्रता, लाभ और अंतिम तिथि संबंधित आधिकारिक पोर्टल पर जाँचें।",
    hero_eyebrow:"स्मार्ट नागरिक सहायक",hero_title:"सरकारी सहायता,",hero_title_accent:"अब आसान।",hero_lead:"AI JanSeva सरकारी योजनाओं, सार्वजनिक सेवाओं और नागरिकों की रोज़मर्रा की समस्याओं को सरल भाषा में समझने में मदद करता है।",
    hero_cta_schemes:"योजनाएँ देखें ↗",hero_cta_eligibility:"पात्रता जाँचें",hero_proof_1:"✓ 40+ योजना और सेवा कार्ड",hero_proof_2:"✓ आधिकारिक पोर्टल लिंक",hero_proof_3:"✓ कई भाषाओं में सहायता",
    assistant_name:"जनसेवा AI",assistant_subtitle:"नागरिक सहायक",hero_chat_user:"मैं छात्र हूँ। क्या छात्रवृत्ति मिल सकती है?",hero_chat_bot:"आपके राज्य, श्रेणी, कोर्स और पारिवारिक आय के आधार पर छात्रवृत्ति के विकल्प मिल सकते हैं।",
    stat_categories:"श्रेणियाँ",stat_schemes:"योजना कार्ड",stat_access:"वेबसाइट उपलब्ध",chip_education:"🎓 शिक्षा",chip_farmers:"🌾 किसान सहायता",trust_label:"जानकारी की श्रेणियाँ",cat_education:"शिक्षा",cat_healthcare:"स्वास्थ्य",cat_agriculture:"कृषि",cat_employment:"रोज़गार",cat_services:"नागरिक सेवाएँ",
    schemes_eyebrow:"सरकारी योजनाएँ",schemes_title:"ज़रूरी जानकारी,",schemes_title_accent:"एक ही जगह।",schemes_intro:"योजना खोजें, श्रेणी चुनें और आवेदन से पहले आधिकारिक वेबसाइट पर नियम जाँचें।",
    search_placeholder:"योजना, सेवा या शब्द खोजें...",category_aria:"श्रेणी चुनें",all_categories:"सभी श्रेणियाँ",search_button:"खोजें",reset_filters:"फ़िल्टर हटाएँ ↗",
    eligibility_eyebrow:"स्मार्ट प्रोफ़ाइल",eligibility_title:"अपनी नागरिक",eligibility_title_accent:"प्रोफ़ाइल बनाएँ।",eligibility_intro:"योजनाओं और आधिकारिक लिंक के सुझाव पाने के लिए बुनियादी जानकारी भरें। ये सुझाव सरकारी पात्रता का अंतिम निर्णय नहीं हैं।",
    eligibility_point_1:"✓ जाँचने योग्य सुझाव",eligibility_point_2:"✓ आधिकारिक लिंक शामिल",eligibility_point_3:"✓ प्रोफ़ाइल विवरण सेव नहीं होते",profile_title:"नागरिक जानकारी",profile_subtitle:"अपनी बुनियादी जानकारी भरें",field_age:"उम्र",field_income:"वार्षिक पारिवारिक आय (₹)",field_occupation:"व्यवसाय",field_state:"राज्य",field_category:"श्रेणी (वैकल्पिक)",analyze_button:"प्रोफ़ाइल जाँचें ↗",privacy_note:"आपकी जानकारी केवल इस अनुरोध के लिए उपयोग होती है।",
    help_eyebrow:"जनसेवा सहायता",help_title:"सवाल पूछें,",help_title_accent:"सरल जवाब पाएँ।",help_intro:"योजना, दस्तावेज़, छात्रवृत्ति, स्वास्थ्य और किसान सहायता के बारे में पूछें। यह सहायक अभी live generative AI से जुड़ा नहीं है।",
    help_card_title:"नमस्ते! मैं जनसेवा सहायता हूँ।",help_card_intro:"सरकारी योजनाओं, दस्तावेज़ों, छात्रवृत्ति, स्वास्थ्य और किसान सहायता के बारे में पूछें।",prompt_scholarship:"🎓 छात्रवृत्ति",prompt_documents:"🪪 दस्तावेज़",prompt_farmers:"🌾 किसान सहायता",prompt_health:"✚ स्वास्थ्य",chat_panel_title:"जनसेवा सहायता",chat_panel_subtitle:"जानकारी देने वाला सहायक",chat_welcome:"नमस्ते! आज मैं आपकी किस विषय में मदद कर सकता हूँ?",chat_placeholder:"सरकारी सेवा के बारे में पूछें...",chat_disclaimer:"जानकारी की पुष्टि आधिकारिक सरकारी पोर्टल पर करें।",
    faq_eyebrow:"सहायता केंद्र",faq_title:"अक्सर पूछे जाने वाले",faq_title_accent:"सवाल।",faq_intro:"शुरू करने से पहले कुछ ज़रूरी बातें।",faq1_q:"क्या यह सरकारी वेबसाइट है?",faq1_a:"नहीं। AI JanSeva एक शैक्षणिक नागरिक-सहायता प्रोटोटाइप है, सरकारी विभाग या आधिकारिक पोर्टल नहीं।",faq2_q:"क्या वेबसाइट पात्रता की पुष्टि करती है?",faq2_a:"नहीं। यह केवल शुरुआती सुझाव देती है। पात्रता मौजूदा नियमों और आपकी परिस्थितियों पर निर्भर करती है।",faq3_q:"क्या मैं पसंदीदा योजनाएँ सेव कर सकता हूँ?",faq3_a:"हाँ। रजिस्टर और लॉगिन करके योजनाओं को सेव कर सकते हैं।",faq4_q:"क्या AI सहायता live AI से जुड़ी है?",faq4_a:"इस संस्करण में विषय-आधारित सहायता है। Live AI के लिए provider API और सुरक्षित backend configuration चाहिए।",faq5_q:"निजी जानकारी कैसे सुरक्षित रखें?",faq5_a:"OTP, पासवर्ड, UPI PIN या बैंक PIN साझा न करें। आवेदन के लिए आधिकारिक पोर्टल उपयोग करें।",
    loading:"सुझाव तैयार हो रहे हैं…",suggestions_title:"आपकी प्रोफ़ाइल के लिए जाँचने योग्य विकल्प",chat_loading:"जानकारी देखी जा रही है…",chat_error:"सर्वर से संपर्क नहीं हो पाया। दोबारा प्रयास करें।",no_results:"कोई योजना नहीं मिली",no_results_help:"दूसरा शब्द या श्रेणी चुनकर देखें।",view_all:"सभी योजनाएँ देखें"
  },
  bn: {
    problems_eyebrow:'দৈনন্দিন সমস্যা',
    problems_title:'দৈনন্দিন সহায়তা, এক জায়গায়।',
    problems_intro:'ভারতের নাগরিক ও শিক্ষার্থীদের সাধারণ সমস্যা।',
    problem_scholarships:'বৃত্তি',
    problem_scholarships_desc:'বৃত্তির সুযোগ ও প্রাথমিক যোগ্যতা সম্পর্কে জানুন।',
    problem_documents:'নথি',
    problem_documents_desc:'সাধারণ নথি ও নাগরিক পরিষেবা সম্পর্কে নির্দেশনা পান।',
    problem_health:'স্বাস্থ্যসেবা',
    problem_health_desc:'সরকারি স্বাস্থ্য প্রকল্প ও পরিষেবা সম্পর্কে জানুন।',
    problem_farmers:'কৃষক সহায়তা',
    problem_farmers_desc:'কৃষি সহায়তা ও কৃষকদের জন্য প্রকল্প দেখুন।',
    nav_problems:"সমস্যা",nav_schemes:"প্রকল্প",nav_eligibility:"যোগ্যতা",nav_help:"AI সহায়তা",nav_saved:"সংরক্ষিত প্রকল্প",nav_login:"লগইন",nav_register:"নিবন্ধন",nav_logout:"লগআউট",nav_greeting:"স্বাগতম",
    footer_tagline:"সরকারি তথ্য, সহজ ভাষায়।",footer_note:"AI JanSeva একটি শিক্ষামূলক প্রকল্প, সরকারি ওয়েবসাইট নয়। যোগ্যতা ও শেষ তারিখ সরকারি পোর্টালে যাচাই করুন।",
    hero_eyebrow:"স্মার্ট নাগরিক সহায়ক",hero_title:"সরকারি সহায়তা,",hero_title_accent:"এখন সহজ।",hero_lead:"AI JanSeva সরকারি প্রকল্প, জনসেবা এবং নাগরিকদের দৈনন্দিন সমস্যা সহজ ভাষায় বুঝতে সাহায্য করে।",
    hero_cta_schemes:"প্রকল্প দেখুন ↗",hero_cta_eligibility:"যোগ্যতা যাচাই",hero_proof_1:"✓ ৪০+ প্রকল্প ও পরিষেবা",hero_proof_2:"✓ সরকারি পোর্টাল লিঙ্ক",hero_proof_3:"✓ একাধিক ভাষা",
    assistant_name:"জনসেবা AI",assistant_subtitle:"নাগরিক সহায়ক",hero_chat_user:"আমি একজন ছাত্র। বৃত্তি আছে কি?",hero_chat_bot:"আপনার রাজ্য, বিভাগ, কোর্স এবং পারিবারিক আয়ের উপর বৃত্তির সুযোগ নির্ভর করতে পারে।",
    stat_categories:"বিভাগ",stat_schemes:"প্রকল্প কার্ড",stat_access:"ওয়েবসাইট অ্যাক্সেস",chip_education:"🎓 শিক্ষা",chip_farmers:"🌾 কৃষক সহায়তা",trust_label:"তথ্যের বিভাগ",cat_education:"শিক্ষা",cat_healthcare:"স্বাস্থ্য",cat_agriculture:"কৃষি",cat_employment:"কর্মসংস্থান",cat_services:"নাগরিক পরিষেবা",
    schemes_eyebrow:"সরকারি প্রকল্প",schemes_title:"আপনার প্রয়োজনীয় সবকিছু,",schemes_title_accent:"এক জায়গায়।",schemes_intro:"প্রকল্প খুঁজুন, বিভাগ বেছে নিন এবং আবেদন করার আগে সরকারি ওয়েবসাইটে নিয়ম যাচাই করুন।",
    search_placeholder:"প্রকল্প বা পরিষেবা খুঁজুন...",category_aria:"বিভাগ বেছে নিন",all_categories:"সব বিভাগ",search_button:"খুঁজুন",reset_filters:"ফিল্টার মুছুন ↗",
    eligibility_eyebrow:"স্মার্ট প্রোফাইল",eligibility_title:"আপনার নাগরিক",eligibility_title_accent:"প্রোফাইল তৈরি করুন।",eligibility_intro:"সম্ভাব্য প্রকল্পের পরামর্শ পেতে প্রাথমিক তথ্য দিন। এটি সরকারি যোগ্যতার চূড়ান্ত সিদ্ধান্ত নয়।",
    eligibility_point_1:"✓ প্রাথমিক পরামর্শ",eligibility_point_2:"✓ সরকারি লিঙ্ক",eligibility_point_3:"✓ তথ্য সংরক্ষণ করা হয় না",profile_title:"নাগরিকের তথ্য",profile_subtitle:"আপনার প্রাথমিক তথ্য দিন",field_age:"বয়স",field_income:"বার্ষিক পারিবারিক আয় (₹)",field_occupation:"পেশা",field_state:"রাজ্য",field_category:"বিভাগ (ঐচ্ছিক)",analyze_button:"প্রোফাইল বিশ্লেষণ ↗",privacy_note:"আপনার তথ্য শুধু এই অনুরোধে ব্যবহার করা হয়।",
    help_eyebrow:"জনসেবা সহায়তা",help_title:"প্রশ্ন করুন,",help_title_accent:"সহজ উত্তর পান।",help_intro:"প্রকল্প, নথি, বৃত্তি, স্বাস্থ্য ও কৃষক সহায়তা সম্পর্কে প্রশ্ন করুন। এটি live generative AI-এর সঙ্গে যুক্ত নয়।",
    help_card_title:"নমস্কার! আমি জনসেবা সহায়তা।",help_card_intro:"সরকারি প্রকল্প, নথি, বৃত্তি, স্বাস্থ্য ও কৃষক সহায়তা সম্পর্কে জিজ্ঞাসা করুন।",prompt_scholarship:"🎓 বৃত্তি",prompt_documents:"🪪 নথি",prompt_farmers:"🌾 কৃষক সহায়তা",prompt_health:"✚ স্বাস্থ্য",chat_panel_title:"জনসেবা সহায়তা",chat_panel_subtitle:"তথ্য সহায়ক",chat_welcome:"নমস্কার! আজ কীভাবে সাহায্য করতে পারি?",chat_placeholder:"সরকারি পরিষেবা সম্পর্কে জিজ্ঞাসা করুন...",chat_disclaimer:"সরকারি পোর্টালে তথ্য যাচাই করুন।",
    faq_eyebrow:"সহায়তা কেন্দ্র",faq_title:"প্রায়শই জিজ্ঞাসিত",faq_title_accent:"প্রশ্ন।",faq_intro:"শুরু করার আগে কয়েকটি গুরুত্বপূর্ণ বিষয়।",faq1_q:"এটি কি সরকারি ওয়েবসাইট?",faq1_a:"না। AI JanSeva একটি শিক্ষামূলক প্রকল্প, সরকারি বিভাগ বা পোর্টাল নয়।",faq2_q:"ওয়েবসাইট কি যোগ্যতা নিশ্চিত করে?",faq2_a:"না। এটি প্রাথমিক পরামর্শ দেয়। যোগ্যতা বর্তমান নিয়ম ও ব্যক্তিগত পরিস্থিতির উপর নির্ভর করে।",faq3_q:"আমি কি পছন্দের প্রকল্প সংরক্ষণ করতে পারি?",faq3_a:"হ্যাঁ। নিবন্ধন করে লগইন করুন এবং প্রকল্প সংরক্ষণ করুন।",faq4_q:"AI সহায়তা কি live AI-এর সঙ্গে যুক্ত?",faq4_a:"এই সংস্করণে বিষয়ভিত্তিক সহায়তা আছে। Live AI-এর জন্য API প্রয়োজন।",faq5_q:"ব্যক্তিগত তথ্য কীভাবে সুরক্ষিত রাখব?",faq5_a:"OTP, পাসওয়ার্ড বা ব্যাংক PIN শেয়ার করবেন না। সরকারি পোর্টাল ব্যবহার করুন।",
    loading:"পরামর্শ তৈরি হচ্ছে…",suggestions_title:"আপনার প্রোফাইলের জন্য বিকল্প",chat_loading:"তথ্য দেখা হচ্ছে…",chat_error:"সার্ভারের সঙ্গে যোগাযোগ করা যায়নি। আবার চেষ্টা করুন।",no_results:"কোনও প্রকল্প পাওয়া যায়নি",no_results_help:"অন্য শব্দ বা বিভাগ চেষ্টা করুন।",view_all:"সব প্রকল্প দেখুন"
  },
  ta: {
    problems_eyebrow:'அன்றாடப் பிரச்சினைகள்',
    problems_title:'அன்றாட உதவி, ஒரே இடத்தில்.',
    problems_intro:'இந்திய குடிமக்கள் மற்றும் மாணவர்கள் எதிர்கொள்ளும் பொதுவான பிரச்சினைகள்.',
    problem_scholarships:'உதவித்தொகைகள்',
    problem_scholarships_desc:'உதவித்தொகை வாய்ப்புகள் மற்றும் அடிப்படைத் தகுதியைப் புரிந்துகொள்ளுங்கள்.',
    problem_documents:'ஆவணங்கள்',
    problem_documents_desc:'பொதுவான ஆவணங்கள் மற்றும் குடிமக்கள் சேவைகள் பற்றிய வழிகாட்டல் பெறுங்கள்.',
    problem_health:'சுகாதாரம்',
    problem_health_desc:'அரசு சுகாதாரத் திட்டங்கள் மற்றும் சேவைகளைப் பற்றி அறியுங்கள்.',
    problem_farmers:'விவசாயி உதவி',
    problem_farmers_desc:'விவசாய உதவி மற்றும் விவசாயிகளுக்கான திட்டங்களைப் பாருங்கள்.',
    nav_problems:"சிக்கல்கள்",nav_schemes:"திட்டங்கள்",nav_eligibility:"தகுதி",nav_help:"AI உதவி",nav_saved:"சேமித்த திட்டங்கள்",nav_login:"உள்நுழை",nav_register:"பதிவு",nav_logout:"வெளியேறு",nav_greeting:"வணக்கம்",
    footer_tagline:"அரசுத் தகவல்கள், எளிய மொழியில்.",footer_note:"AI JanSeva ஒரு கல்வித் திட்டம்; அரசின் அதிகாரப்பூர்வ இணையதளம் அல்ல. தகுதி மற்றும் காலக்கெடுவை அதிகாரப்பூர்வ தளத்தில் சரிபார்க்கவும்.",
    hero_eyebrow:"ஸ்மார்ட் குடிமக்கள் உதவியாளர்",hero_title:"அரசு உதவி,",hero_title_accent:"இப்போது எளிது.",hero_lead:"அரசுத் திட்டங்கள், பொதுச் சேவைகள் மற்றும் அன்றாட குடிமக்கள் பிரச்சினைகளை எளிய மொழியில் புரிந்துகொள்ள AI JanSeva உதவுகிறது.",
    hero_cta_schemes:"திட்டங்களைப் பார்க்க ↗",hero_cta_eligibility:"தகுதியைச் சரிபார்",hero_proof_1:"✓ 40+ திட்டங்கள் மற்றும் சேவைகள்",hero_proof_2:"✓ அதிகாரப்பூர்வ இணைப்புகள்",hero_proof_3:"✓ பல மொழிகள்",
    assistant_name:"ஜன்சேவா AI",assistant_subtitle:"குடிமக்கள் உதவியாளர்",hero_chat_user:"நான் மாணவர். உதவித்தொகை உள்ளதா?",hero_chat_bot:"உங்கள் மாநிலம், பிரிவு, படிப்பு மற்றும் குடும்ப வருமானத்தைப் பொறுத்து உதவித்தொகை வாய்ப்புகள் இருக்கலாம்.",
    stat_categories:"வகைகள்",stat_schemes:"திட்ட அட்டைகள்",stat_access:"இணையதள அணுகல்",chip_education:"🎓 கல்வி",chip_farmers:"🌾 விவசாயி உதவி",trust_label:"தகவல் வகைகள்",cat_education:"கல்வி",cat_healthcare:"சுகாதாரம்",cat_agriculture:"விவசாயம்",cat_employment:"வேலைவாய்ப்பு",cat_services:"குடிமக்கள் சேவைகள்",
    schemes_eyebrow:"அரசுத் திட்டங்கள்",schemes_title:"உங்களுக்குத் தேவையான அனைத்தும்,",schemes_title_accent:"ஒரே இடத்தில்.",schemes_intro:"திட்டங்களைத் தேடி, வகையைத் தேர்ந்தெடுத்து, விண்ணப்பிக்கும் முன் அதிகாரப்பூர்வ இணையதளத்தில் விதிகளைச் சரிபார்க்கவும்.",
    search_placeholder:"திட்டங்கள் அல்லது சேவைகளைத் தேடுங்கள்...",category_aria:"வகையைத் தேர்ந்தெடு",all_categories:"அனைத்து வகைகள்",search_button:"தேடு",reset_filters:"வடிகட்டியை நீக்கு ↗",
    eligibility_eyebrow:"ஸ்மார்ட் சுயவிவரம்",eligibility_title:"உங்கள் குடிமக்கள்",eligibility_title_accent:"சுயவிவரத்தை உருவாக்குங்கள்.",eligibility_intro:"சரிபார்க்க வேண்டிய திட்டங்களை அறிய அடிப்படைத் தகவல்களை உள்ளிடுங்கள். இது அதிகாரப்பூர்வ தகுதி முடிவு அல்ல.",
    eligibility_point_1:"✓ ஆரம்ப பரிந்துரைகள்",eligibility_point_2:"✓ அதிகாரப்பூர்வ இணைப்புகள்",eligibility_point_3:"✓ விவரங்கள் சேமிக்கப்படாது",profile_title:"குடிமக்கள் தகவல்",profile_subtitle:"அடிப்படை விவரங்களை உள்ளிடுங்கள்",field_age:"வயது",field_income:"ஆண்டு குடும்ப வருமானம் (₹)",field_occupation:"தொழில்",field_state:"மாநிலம்",field_category:"பிரிவு (விருப்பம்)",analyze_button:"சுயவிவரத்தைப் பகுப்பாய்வு செய் ↗",privacy_note:"உங்கள் தகவல் இந்தக் கோரிக்கைக்காக மட்டுமே பயன்படுத்தப்படும்.",
    help_eyebrow:"ஜன்சேவா உதவி",help_title:"கேள்வி கேளுங்கள்,",help_title_accent:"எளிய பதில் பெறுங்கள்.",help_intro:"திட்டங்கள், ஆவணங்கள், உதவித்தொகை, சுகாதாரம் மற்றும் விவசாய உதவி பற்றி கேளுங்கள். இது நேரடி generative AI-யுடன் இணைக்கப்படவில்லை.",
    help_card_title:"வணக்கம்! நான் ஜன்சேவா உதவி.",help_card_intro:"அரசுத் திட்டங்கள், ஆவணங்கள், உதவித்தொகை, சுகாதாரம் மற்றும் விவசாய உதவி பற்றி கேளுங்கள்.",prompt_scholarship:"🎓 உதவித்தொகை",prompt_documents:"🪪 ஆவணங்கள்",prompt_farmers:"🌾 விவசாயி உதவி",prompt_health:"✚ சுகாதாரம்",chat_panel_title:"ஜன்சேவா உதவி",chat_panel_subtitle:"தகவல் வழிகாட்டி",chat_welcome:"வணக்கம்! இன்று எவ்வாறு உதவலாம்?",chat_placeholder:"அரசுச் சேவை பற்றி கேளுங்கள்...",chat_disclaimer:"அதிகாரப்பூர்வ அரசுத் தளத்தில் தகவலைச் சரிபார்க்கவும்.",
    faq_eyebrow:"உதவி மையம்",faq_title:"அடிக்கடி கேட்கப்படும்",faq_title_accent:"கேள்விகள்.",faq_intro:"தொடங்குவதற்கு முன் சில முக்கிய விஷயங்கள்.",faq1_q:"இது அரசின் அதிகாரப்பூர்வ இணையதளமா?",faq1_a:"இல்லை. AI JanSeva ஒரு கல்வி முன்மாதிரி; அரசுத் துறை அல்லது அதிகாரப்பூர்வ தளம் அல்ல.",faq2_q:"இணையதளம் தகுதியை உறுதிப்படுத்துமா?",faq2_a:"இல்லை. இது ஆரம்ப பரிந்துரைகளை மட்டுமே வழங்குகிறது.",faq3_q:"பிடித்த திட்டங்களைச் சேமிக்கலாமா?",faq3_a:"ஆம். பதிவு செய்து உள்நுழைந்து திட்டங்களைச் சேமிக்கலாம்.",faq4_q:"AI உதவி நேரடி AI-யுடன் இணைக்கப்பட்டுள்ளதா?",faq4_a:"இந்த பதிப்பில் தலைப்பு அடிப்படையிலான வழிகாட்டுதல் உள்ளது. நேரடி AI-க்கு API தேவை.",faq5_q:"தனிப்பட்ட தகவலை எவ்வாறு பாதுகாப்பது?",faq5_a:"OTP, கடவுச்சொல் அல்லது வங்கி PIN-ஐப் பகிர வேண்டாம். அதிகாரப்பூர்வ தளங்களைப் பயன்படுத்துங்கள்.",
    loading:"பரிந்துரைகள் தயாராகின்றன…",suggestions_title:"உங்கள் சுயவிவரத்திற்கான விருப்பங்கள்",chat_loading:"தகவல் சரிபார்க்கப்படுகிறது…",chat_error:"சேவையகத்தைத் தொடர்புகொள்ள முடியவில்லை. மீண்டும் முயற்சிக்கவும்.",no_results:"திட்டங்கள் கிடைக்கவில்லை",no_results_help:"வேறு சொல் அல்லது வகையை முயற்சிக்கவும்.",view_all:"அனைத்து திட்டங்களையும் காண்க"
  },
  te: {
    problems_eyebrow:'రోజువారీ సమస్యలు',
    problems_title:'రోజువారీ సహాయం, ఒకే చోట.',
    problems_intro:'భారత పౌరులు మరియు విద్యార్థులు ఎదుర్కొనే సాధారణ సమస్యలు.',
    problem_scholarships:'స్కాలర్\u200cషిప్\u200cలు',
    problem_scholarships_desc:'స్కాలర్\u200cషిప్ అవకాశాలు మరియు ప్రాథమిక అర్హత గురించి తెలుసుకోండి.',
    problem_documents:'పత్రాలు',
    problem_documents_desc:'సాధారణ పత్రాలు మరియు పౌర సేవల గురించి మార్గదర్శకం పొందండి.',
    problem_health:'ఆరోగ్య సేవలు',
    problem_health_desc:'ప్రభుత్వ ఆరోగ్య పథకాలు మరియు సేవల గురించి తెలుసుకోండి.',
    problem_farmers:'రైతు సహాయం',
    problem_farmers_desc:'వ్యవసాయ సహాయం మరియు రైతుల పథకాలను చూడండి.',
    nav_problems:"సమస్యలు",nav_schemes:"పథకాలు",nav_eligibility:"అర్హత",nav_help:"AI సహాయం",nav_saved:"సేవ్ చేసిన పథకాలు",nav_login:"లాగిన్",nav_register:"నమోదు",nav_logout:"లాగ్ అవుట్",nav_greeting:"స్వాగతం",
    footer_tagline:"ప్రభుత్వ సమాచారం, సులభమైన భాషలో.",footer_note:"AI JanSeva విద్యా ప్రాజెక్ట్ మాత్రమే; అధికారిక ప్రభుత్వ వెబ్‌సైట్ కాదు. అర్హత, ప్రయోజనాలు, గడువులను అధికారిక పోర్టల్‌లో నిర్ధారించండి.",
    hero_eyebrow:"స్మార్ట్ పౌర సహాయకుడు",hero_title:"ప్రభుత్వ సహాయం,",hero_title_accent:"ఇప్పుడు సులభం.",hero_lead:"ప్రభుత్వ పథకాలు, ప్రజా సేవలు మరియు రోజువారీ పౌర సమస్యలను సులభంగా అర్థం చేసుకోవడానికి AI JanSeva సహాయపడుతుంది.",
    hero_cta_schemes:"పథకాలు చూడండి ↗",hero_cta_eligibility:"అర్హత చూడండి",hero_proof_1:"✓ 40+ పథకాలు మరియు సేవలు",hero_proof_2:"✓ అధికారిక పోర్టల్ లింకులు",hero_proof_3:"✓ అనేక భాషలు",
    assistant_name:"జన్‌సేవా AI",assistant_subtitle:"పౌర సహాయకుడు",hero_chat_user:"నేను విద్యార్థిని. స్కాలర్‌షిప్‌లు ఉన్నాయా?",hero_chat_bot:"మీ రాష్ట్రం, వర్గం, కోర్సు మరియు కుటుంబ ఆదాయం ఆధారంగా స్కాలర్‌షిప్ అవకాశాలు ఉండవచ్చు.",
    stat_categories:"వర్గాలు",stat_schemes:"పథకాల కార్డులు",stat_access:"వెబ్‌సైట్ అందుబాటు",chip_education:"🎓 విద్య",chip_farmers:"🌾 రైతు సహాయం",trust_label:"సమాచార వర్గాలు",cat_education:"విద్య",cat_healthcare:"ఆరోగ్యం",cat_agriculture:"వ్యవసాయం",cat_employment:"ఉద్యోగాలు",cat_services:"పౌర సేవలు",
    schemes_eyebrow:"ప్రభుత్వ పథకాలు",schemes_title:"మీకు అవసరమైనది అంతా,",schemes_title_accent:"ఒకే చోట.",schemes_intro:"పథకాలను వెతికి, వర్గాన్ని ఎంచుకుని, దరఖాస్తు ముందు అధికారిక వెబ్‌సైట్‌లో నియమాలు చూడండి.",
    search_placeholder:"పథకాలు లేదా సేవలను వెతకండి...",category_aria:"వర్గాన్ని ఎంచుకోండి",all_categories:"అన్ని వర్గాలు",search_button:"వెతకండి",reset_filters:"ఫిల్టర్లను తొలగించండి ↗",
    eligibility_eyebrow:"స్మార్ట్ ప్రొఫైల్",eligibility_title:"మీ పౌర",eligibility_title_accent:"ప్రొఫైల్ రూపొందించండి.",eligibility_intro:"చూడదగిన పథకాల సూచనల కోసం ప్రాథమిక వివరాలు నమోదు చేయండి. ఇది అధికారిక అర్హత నిర్ణయం కాదు.",
    eligibility_point_1:"✓ ప్రాథమిక సూచనలు",eligibility_point_2:"✓ అధికారిక లింకులు",eligibility_point_3:"✓ వివరాలు నిల్వ చేయబడవు",profile_title:"పౌర సమాచారం",profile_subtitle:"మీ ప్రాథమిక వివరాలు నమోదు చేయండి",field_age:"వయస్సు",field_income:"వార్షిక కుటుంబ ఆదాయం (₹)",field_occupation:"వృత్తి",field_state:"రాష్ట్రం",field_category:"వర్గం (ఐచ్ఛికం)",analyze_button:"ప్రొఫైల్ విశ్లేషించండి ↗",privacy_note:"మీ సమాచారం ఈ అభ్యర్థన కోసం మాత్రమే ఉపయోగించబడుతుంది.",
    help_eyebrow:"జన్‌సేవా సహాయం",help_title:"ప్రశ్న అడగండి,",help_title_accent:"సులభమైన సమాధానం పొందండి.",help_intro:"పథకాలు, పత్రాలు, స్కాలర్‌షిప్‌లు, ఆరోగ్యం మరియు రైతు సహాయం గురించి అడగండి. ఇది live generative AIతో అనుసంధానించబడలేదు.",
    help_card_title:"నమస్కారం! నేను జన్‌సేవా సహాయం.",help_card_intro:"ప్రభుత్వ పథకాలు, పత్రాలు, స్కాలర్‌షిప్‌లు, ఆరోగ్యం మరియు రైతు సహాయం గురించి అడగండి.",prompt_scholarship:"🎓 స్కాలర్‌షిప్‌లు",prompt_documents:"🪪 పత్రాలు",prompt_farmers:"🌾 రైతు సహాయం",prompt_health:"✚ ఆరోగ్యం",chat_panel_title:"జన్‌సేవా సహాయం",chat_panel_subtitle:"సమాచార మార్గదర్శి",chat_welcome:"నమస్కారం! ఈరోజు మీకు ఎలా సహాయం చేయగలను?",chat_placeholder:"ప్రభుత్వ సేవ గురించి అడగండి...",chat_disclaimer:"అధికారిక ప్రభుత్వ పోర్టల్‌లో సమాచారాన్ని నిర్ధారించండి.",
    faq_eyebrow:"సహాయ కేంద్రం",faq_title:"తరచుగా అడిగే",faq_title_accent:"ప్రశ్నలు.",faq_intro:"ప్రారంభించే ముందు కొన్ని ముఖ్యమైన విషయాలు.",faq1_q:"ఇది అధికారిక ప్రభుత్వ వెబ్‌సైటా?",faq1_a:"కాదు. AI JanSeva ఒక విద్యా ప్రాజెక్ట్ మాత్రమే; ప్రభుత్వ శాఖ లేదా అధికారిక పోర్టల్ కాదు.",faq2_q:"ఈ వెబ్‌సైట్ అర్హతను నిర్ధారిస్తుందా?",faq2_a:"కాదు. ఇది ప్రాథమిక సూచనలు మాత్రమే ఇస్తుంది.",faq3_q:"నాకు నచ్చిన పథకాలను సేవ్ చేయవచ్చా?",faq3_a:"అవును. నమోదు చేసి లాగిన్ అయి పథకాలను సేవ్ చేయండి.",faq4_q:"AI సహాయం live AIతో అనుసంధానించబడిందా?",faq4_a:"ఈ సంచికలో అంశాల ఆధారిత మార్గదర్శకం ఉంది. Live AIకి API అవసరం.",faq5_q:"వ్యక్తిగత సమాచారాన్ని ఎలా కాపాడుకోవాలి?",faq5_a:"OTP, పాస్‌వర్డ్ లేదా బ్యాంక్ PIN పంచుకోవద్దు. అధికారిక పోర్టల్‌లను ఉపయోగించండి.",
    loading:"సూచనలు సిద్ధమవుతున్నాయి…",suggestions_title:"మీ ప్రొఫైల్ కోసం చూడదగిన ఎంపికలు",chat_loading:"సమాచారం పరిశీలిస్తోంది…",chat_error:"సర్వర్‌ను సంప్రదించలేకపోయాం. మళ్లీ ప్రయత్నించండి.",no_results:"పథకాలు కనబడలేదు",no_results_help:"మరొక పదం లేదా వర్గాన్ని ప్రయత్నించండి.",view_all:"అన్ని పథకాలు చూడండి"
  }
};

function applyJanSevaLanguage(lang) {
  const dictionary = JANSEVA_I18N[lang] || JANSEVA_I18N.en;
  document.documentElement.lang = lang;
  document.documentElement.dataset.language = lang;
  try { localStorage.setItem("janseva-language", lang); } catch (_) {}
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.i18n;
    if (dictionary[key] !== undefined) {
      // Preserve the arrow/icon span when translating buttons.
      const icon = element.querySelector(":scope > span");
      if (icon && /hero_cta|analyze_button/.test(key)) {
        const label = dictionary[key].replace(/\s*↗$/, "");
        element.firstChild.textContent = label + " ";
      } else {
        element.textContent = dictionary[key];
      }
    }
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const value = dictionary[element.dataset.i18nPlaceholder];
    if (value) element.placeholder = value;
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
    const value = dictionary[element.dataset.i18nAria];
    if (value) element.setAttribute("aria-label", value);
  });
  document.querySelectorAll("#mainNav .nav-user").forEach((element) => {
    const username = element.textContent.replace(/^(Welcome|नमस्ते|স্বাগতম|வணக்கம்|స్వాగతం),?\s*/i, "");
    const prefix = dictionary.nav_greeting || "Welcome";
    element.textContent = prefix + ", " + username.trim();
  });
  const form = document.getElementById("eligibilityForm");
  if (form) {
    const button = form.querySelector('button[type="submit"]');
    if (button && !button.disabled) {
      button.innerHTML = (dictionary.analyze_button || "Analyze Profile") + ' <span>↗</span>';
    }
  }
  const chatInput = document.getElementById("chatInput");
  if (chatInput) chatInput.placeholder = dictionary.chat_placeholder || chatInput.placeholder;
}
document.addEventListener("DOMContentLoaded", () => {
  const selector = document.getElementById("languageSelect");
  let saved = "en";
  try { saved = localStorage.getItem("janseva-language") || "en"; } catch (_) {}
  if (selector) {
    selector.value = JANSEVA_I18N[saved] ? saved : "en";
    applyJanSevaLanguage(selector.value);
    selector.addEventListener("change", () => applyJanSevaLanguage(selector.value));
  } else {
    applyJanSevaLanguage(saved);
  }
});
