import{j as e}from"./jsx-runtime.D_zvdyIk.js";import{r as a}from"./index.C5BVv2q5.js";const v="https://webhook.tiroltourismus.com/api/newsletter";function z({compact:n=!1}){const[t,s]=a.useState(""),[c,p]=a.useState(""),[x,d]=a.useState(!1),[o,i]=a.useState("idle"),[g,l]=a.useState(""),[u,m]=a.useState("");function b(){return!t.trim()||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(t.trim())?(l("Bitte gib eine gültige E-Mail-Adresse ein."),!1):x?!0:(l("Bitte stimme der Datenschutzerklärung zu."),!1)}async function f(){try{return(await fetch(v,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:t.trim(),name:c.trim()})})).ok}catch{return!1}}async function h(){return!1}async function k(r){if(r.preventDefault(),l(""),!b()){i("error");return}if(i("loading"),m(t.trim()),await f()){i("success"),s(""),p(""),d(!1);return}await h()?(i("success"),s(""),p(""),d(!1)):(l("Fehler bei der Anmeldung. Bitte versuche es später erneut."),i("error"))}return e.jsxs(e.Fragment,{children:[e.jsx("style",{children:`
        .nl-root {
          --nl-bg: linear-gradient(135deg, rgba(255,20,147,.06), rgba(212,168,0,.06));
          --nl-border: 1px solid rgba(255,255,255,.08);
          --nl-radius: 16px;
          --nl-gap: 12px;
        }
        .nl-root.nl-compact {
          text-align: left;
          padding: 0;
        }
        .nl-root.nl-compact .nl-form-wrap {
          gap: 10px;
        }
        .nl-root.nl-compact .nl-row {
          display: flex;
          gap: 10px;
          align-items: stretch;
        }
        .nl-root.nl-compact .nl-input {
          flex: 1;
          padding: 11px 14px;
          border-radius: 999px;
          border: 1px solid rgba(255,255,255,.12);
          background: rgba(255,255,255,.06);
          color: var(--text, #F0EDEE);
          font-size: 12px;
          font-family: var(--font-body, 'Montserrat', sans-serif);
          backdrop-filter: blur(10px);
          transition: all .3s;
          min-width: 0;
        }
        .nl-root.nl-compact .nl-input::placeholder { color: rgba(255,255,255,.32); }
        .nl-root.nl-compact .nl-input:focus { border-color: var(--pink, #FF1493); background: rgba(255,255,255,.1); box-shadow: 0 0 0 3px rgba(255,20,147,.12); }
        .nl-root.nl-compact .nl-input.error { border-color: #ff4444; }

        .nl-submit {
          padding: 12px 24px;
          border-radius: 100px;
          border: none;
          background: linear-gradient(135deg, var(--pink, #FF1493), var(--pink-dark, #C0006E));
          color: #fff;
          font-size: 12px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: .5px;
          cursor: pointer;
          transition: all .3s cubic-bezier(.16,1,.3,1);
          white-space: nowrap;
          font-family: var(--font-body, 'Montserrat', sans-serif);
          display: inline-flex;
          align-items: center;
          gap: 6px;
          justify-content: center;
        }
        .nl-root.nl-compact .nl-submit {
          padding: 11px 16px;
          font-size: 11px;
          letter-spacing: .35px;
        }
        .nl-submit:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(255,20,147,.35); }
        .nl-submit:disabled { opacity: .5; cursor: not-allowed; transform: none; box-shadow: none; }
        .nl-submit.gold {
          background: linear-gradient(135deg, var(--gold, #D4A800), var(--gold-light, #FFD700));
          color: #1a1a1a;
        }
        .nl-submit.gold:hover { box-shadow: 0 6px 24px rgba(212,168,0,.35); }

        .nl-spinner {
          display: inline-block;
          width: 14px; height: 14px;
          border: 2px solid rgba(255,255,255,.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: nl-spin .6s linear infinite;
        }
        @keyframes nl-spin { to { transform: rotate(360deg); } }

        .nl-state {
          padding: 16px 20px;
          border-radius: 12px;
          font-size: 14px;
          line-height: 1.5;
          text-align: center;
          animation: nl-fadeIn .3s ease;
        }
        .nl-state.success {
          background: rgba(0,200,83,.12);
          border: 1px solid rgba(0,200,83,.25);
          color: #00E676;
        }
        .nl-state.error {
          background: rgba(255,68,68,.1);
          border: 1px solid rgba(255,68,68,.2);
          color: #FF6B6B;
        }
        .nl-state .nl-email {
          font-weight: 700;
          word-break: break-all;
        }
        .nl-state strong { display: block; margin-bottom: 4px; font-size: 15px; }
        .nl-state p { margin: 0; font-size: 13px; }

        .nl-checkbox {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          font-size: 11px;
          line-height: 1.5;
          color: rgba(255,255,255,.55);
          cursor: pointer;
        }
        .nl-checkbox input {
          margin-top: 2px;
          width: 16px; height: 16px;
          accent-color: var(--pink, #FF1493);
          cursor: pointer;
          flex-shrink: 0;
        }
        .nl-checkbox a {
          color: var(--gold-light, #FFD700);
          text-decoration: underline;
          text-underline-offset: 2px;
        }
        .nl-checkbox a:hover { color: var(--gold, #D4A800); }

        @keyframes nl-fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── Extra Name-Feld nur bei voller Version ── */
        .nl-name-row {
          display: flex;
          gap: 8px;
        }
        .nl-name-row .nl-input { flex: 1; }

        /* ── Full Hero Style ── */
        .nl-hero {
          position: relative;
          padding: 80px 0;
          text-align: center;
          overflow: hidden;
        }
        .nl-hero::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(135deg, var(--pink, #FF1493), var(--pink-dark, #C0006E));
          opacity: .92;
          pointer-events: none;
        }
        .nl-hero::after {
          content: '';
          position: absolute;
          inset: 0;
          background-image: radial-gradient(circle, rgba(255,255,255,.06) 1.5px, transparent 1.5px);
          background-size: 20px 20px;
          pointer-events: none;
        }
        .nl-hero .nl-inner {
          position: relative;
          z-index: 1;
          max-width: 560px;
          margin: 0 auto;
        }
        .nl-hero h2 {
          font-family: var(--font-display, 'Bebas Neue', Impact, sans-serif);
          font-size: clamp(42px, 8vw, 90px);
          line-height: .9;
          letter-spacing: 2px;
          text-transform: uppercase;
          color: #fff;
          margin-bottom: 4px;
        }
        .nl-hero h2 .gold {
          background: linear-gradient(135deg, var(--gold-light, #FFD700), #fff);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        .nl-hero p {
          font-size: 15px;
          color: rgba(255,255,255,.75);
          margin-bottom: 28px;
          line-height: 1.6;
        }
        .nl-hero .nl-form-wrap {
          max-width: 480px;
          margin: 0 auto;
        }
        .nl-hero .nl-row {
          background: rgba(255,255,255,.1);
          padding: 4px;
          border-radius: 100px;
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255,255,255,.1);
        }
        .nl-hero .nl-input {
          background: transparent;
          border: none;
          color: #fff;
          padding: 14px 20px;
          font-size: 14px;
        }
        .nl-hero .nl-input::placeholder { color: rgba(255,255,255,.4); }
        .nl-hero .nl-submit {
          padding: 14px 28px;
          background: #fff;
          color: var(--pink-dark, #C0006E);
          font-size: 12px;
        }
        .nl-hero .nl-submit:hover { box-shadow: 0 8px 30px rgba(0,0,0,.3); }

        /* ── Compact Footer Style ── */
        .nl-compact .nl-row {
          display: flex;
          gap: 6px;
        }
        .nl-compact .nl-input {
          padding: 10px 16px;
          font-size: 12px;
        }
        .nl-compact .nl-submit {
          padding: 10px 18px;
          font-size: 11px;
        }

        @media (max-width: 500px) {
          .nl-row { flex-direction: column; }
          .nl-hero .nl-row { border-radius: 16px; padding: 8px; }
          .nl-name-row { flex-direction: column; }
        }
      `}),e.jsx("div",{className:`nl-root ${n?"nl-compact":"nl-hero"}`,children:e.jsx("div",{className:n?"":"nl-inner",children:e.jsxs("form",{onSubmit:k,noValidate:!0,className:"nl-form-wrap",children:[o==="success"&&e.jsxs("div",{className:"nl-state success",children:[e.jsx("strong",{children:"🎉 Fast geschafft!"}),e.jsxs("p",{children:["Wir haben eine Bestätigungs-Mail an"," ",e.jsx("span",{className:"nl-email",children:u})," gesendet. Bitte klicke den Link darin, um dein Abonnement zu aktivieren."]})]}),o==="error"&&e.jsxs("div",{className:"nl-state error",children:[e.jsx("strong",{children:"✕ Fehler"}),e.jsx("p",{children:g})]}),o!=="success"&&e.jsxs(e.Fragment,{children:[!n&&e.jsxs(e.Fragment,{children:[e.jsxs("h2",{children:["#tiroltourismus ",e.jsx("span",{className:"gold",children:"Newsletter"})]}),e.jsx("p",{children:"Verpassen Sie keine Neuigkeit aus Tirol. Exklusive Tipps, neue Angebote und Geschichten direkt in Ihr Postfach – jederzeit kündbar."})]}),!n&&e.jsx("div",{className:"nl-name-row",children:e.jsx("input",{type:"text",className:"nl-input",placeholder:"Dein Vorname",value:c,onChange:r=>p(r.target.value),autoComplete:"given-name"})}),e.jsxs("div",{className:"nl-row",children:[e.jsx("input",{type:"email",className:`nl-input${g&&!t.trim()?" error":""}`,placeholder:n?"Deine E-Mail":"deine@email.at",value:t,onChange:r=>s(r.target.value),autoComplete:"email",required:!0}),e.jsx("button",{type:"submit",className:`nl-submit ${n?"":"gold"}`,disabled:o==="loading",children:o==="loading"?e.jsx("span",{className:"nl-spinner"}):n?"Anmelden ✈️":"Kostenlos anmelden"})]}),e.jsxs("label",{className:"nl-checkbox",children:[e.jsx("input",{type:"checkbox",checked:x,onChange:r=>d(r.target.checked)}),e.jsxs("span",{children:["Ich habe die"," ",e.jsx("a",{href:"/datenschutz/",target:"_blank",rel:"noopener noreferrer",children:"Datenschutzerklärung"})," ","gelesen und stimme zu."]})]}),!n&&e.jsx("p",{style:{fontSize:"11px",color:"rgba(255,255,255,.4)",marginTop:"4px"},children:"Mit dem Absenden erklärst du dich mit der Verarbeitung zum Newsletter-Versand einverstanden. Abmeldung jederzeit."})]})]})})})]})}export{z as default};
