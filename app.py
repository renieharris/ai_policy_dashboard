from pathlib import Path
from textwrap import wrap

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='K–12 AI Policy Evidence Lab', layout='wide', initial_sidebar_state='auto')
st.markdown(
    """
    <style>
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] {
            padding-inline: clamp(0.75rem, 4vw, 1.5rem);
        }
        [data-testid="stMainBlockContainer"] h1 {
            font-size: clamp(1.8rem, 6vw, 2.5rem);
            overflow-wrap: anywhere;
        }
        [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
        [data-testid="stMainBlockContainer"] :is([data-testid="stColumn"], [data-testid="column"]) {
            flex: 1 1 auto;
            width: 100%;
            min-width: 0;
        }
        [data-testid="stTabs"] [role="tablist"] {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.25rem;
        }
        [data-testid="stTabs"] [role="tab"] {
            min-height: 44px;
            padding: 0.25rem 0.5rem;
            white-space: normal;
            text-align: center;
        }
        [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            box-shadow: inset 0 -2px currentColor;
        }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            display: none;
        }
        [data-testid="stSidebar"] {
            max-width: 100vw;
        }
        [data-testid="stDownloadButton"] button {
            width: 100%;
            min-height: 44px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title('K–12 AI Policy Evidence Lab')
st.caption('Exploratory dashboard covering video sources, community discourse, and public hearings. Verify source provenance before publishing findings.')

MACRO_STANCE_DEFINITIONS = {
    'Anti-Detector / Due Process Advocate': (
        'Calls for safeguards against AI-based accusations or monitoring. For example, '
        'a school should review a student’s drafts and give them a chance to respond before imposing a penalty.'
    ),
    'Critical / Policy Vacuum & Inconsistency': (
        'Criticizes missing, unclear, or unevenly enforced AI rules. For example, '
        'one teacher allows AI brainstorming while another punishes it.'
    ),
    'Integrationist / Socratic Intellectual Engagement': (
        'Supports using AI to guide students’ thinking. For example, '
        'an AI tutor asks students to explain their reasoning or offers a hint before giving an answer.'
    ),
    'Pro-Integration / Permissive': (
        'Favors allowing and teaching appropriate uses of AI in school, '
        'such as brainstorming, translation, or practicing how to check AI-generated answers.'
    ),
    'Prohibitionist / Restrictive': (
        'Favors banning or tightly limiting certain uses of AI. For example, '
        'a district might block student-facing chatbots in elementary grades.'
    ),
    'Regulatory / Collaborative Governance': (
        'Favors developing clear AI rules with input from the school community. '
        'For example, students and teachers could work together to set classroom expectations for AI use.'
    ),
    'Regulatory / Guardrails-First': (
        'Supports allowing AI once safeguards are in place, such as student privacy protections, '
        'a review of AI tools before adoption, or clear rules for permitted use.'
    ),
    'Regulatory / Labor Protection & Worker Voice': (
        'Prioritizes educators’ say in how AI is used and protects their workload and professional judgment. '
        'For example, teachers should have a say in adoption and retain final judgment over grades.'
    ),
    'Skeptical / Ambivalent': (
        'Expresses doubt or mixed feelings about AI in schools. For example, '
        'someone might see value in lesson planning while worrying about students relying on AI for assignments.'
    ),
}

STANCE_LEGEND_LABELS = {
    'Anti-Detector / Due Process Advocate': 'Due process',
    'Critical / Policy Vacuum & Inconsistency': 'Policy inconsistency',
    'Integrationist / Socratic Intellectual Engagement': 'Socratic learning',
    'Pro-Integration / Permissive': 'Permissive',
    'Prohibitionist / Restrictive': 'Restrictive',
    'Regulatory / Collaborative Governance': 'Shared governance',
    'Regulatory / Guardrails-First': 'Guardrails first',
    'Regulatory / Labor Protection & Worker Voice': 'Educator voice',
    'Skeptical / Ambivalent': 'Skeptical',
}


def show_chart(figure):
    figure.update_layout(
        margin=dict(l=0, r=12, t=12, b=0),
        legend=dict(orientation='h', title_text='', y=-0.2, yanchor='top'),
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config={'responsive': True, 'scrollZoom': False},
    )

@st.cache_data
def load_data():
    d = pd.read_csv(Path(__file__).with_name('master_k12_ai_combined_dataset.csv'))
    d['date'] = pd.to_datetime(d['date'], errors='coerce')
    for col in ['valence', 'arousal']:
        d[col] = pd.to_numeric(d[col], errors='coerce')
    return d

df = load_data()
st.sidebar.header('Filter entries')
selected_groups = st.sidebar.multiselect('Stakeholder group', sorted(df['stakeholder_group'].dropna().unique()), default=sorted(df['stakeholder_group'].dropna().unique()))
selected_aspects = st.sidebar.multiselect('Policy aspect', sorted(df['policy_aspect'].dropna().unique()))
selected_stances = st.sidebar.multiselect(
    'Macro stance', sorted(df['macro_stance'].dropna().unique()),
    help='The broad position expressed in an entry. See the stance definitions in Overview.',
)
search = st.sidebar.text_input('Search summaries and quotes')
f = df[df['stakeholder_group'].isin(selected_groups)].copy()
if selected_aspects:
    f = f[f['policy_aspect'].isin(selected_aspects)]
if selected_stances:
    f = f[f['macro_stance'].isin(selected_stances)]
if search:
    f = f[f['summary_or_quote'].fillna('').str.contains(search, case=False, regex=False)]

if f.empty:
    st.warning('No entries match the current filters.')
    st.stop()

n1,n2,n3 = st.columns(3)
n1.metric('Matching entries', f'{len(f):,}')
n2.metric('Mean valence', f'{f.valence.mean():.2f}')
n3.metric('Mean arousal', f'{f.arousal.mean():.2f}')

overview, evidence, policy, methods = st.tabs(['Overview', 'Explore evidence', 'Policy design studio', 'Methods & limitations'])
with overview:
    st.subheader('Policy stances by stakeholder')
    with st.expander('What do the macro stance labels mean?'):
        st.write('A macro stance is the broad position expressed in an entry. The policy aspect is the specific issue being discussed.')
        for label, definition in MACRO_STANCE_DEFINITIONS.items():
            st.markdown(f'**{label}** ({STANCE_LEGEND_LABELS[label]} in the chart). {definition}')
        st.caption('Definitions draw on the dataset labels and the K–12 AI Policy Executive Briefing and District Guide.')
    counts = f.groupby(['stakeholder_group', 'macro_stance']).size().reset_index(name='count')
    counts['share'] = counts['count'] / counts.groupby('stakeholder_group')['count'].transform('sum')
    counts['chart_stance'] = counts['macro_stance'].replace(STANCE_LEGEND_LABELS)
    counts['chart_group'] = counts['stakeholder_group'].map(lambda label: '<br>'.join(wrap(label, width=15)))
    fig = px.bar(
        counts, x='share', y='chart_group', color='chart_stance', orientation='h',
        barmode='stack', height=420,
        hover_data={'chart_group': False, 'chart_stance': False, 'macro_stance': True, 'stakeholder_group': True, 'count': True},
        labels={'share': 'Share of entries', 'stakeholder_group': 'Stakeholder', 'macro_stance': 'Macro stance'},
    )
    fig.update_xaxes(tickformat='.0%', nticks=5)
    fig.update_yaxes(title_text=None, autorange='reversed')
    show_chart(fig)
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Policy aspects mentioned')
        topic_counts=f['policy_aspect'].value_counts().head(15).reset_index()
        topic_counts.columns=['aspect','count']
        topic_counts['chart_aspect'] = topic_counts['aspect'].map(lambda label: '<br>'.join(wrap(label, width=20)))
        fig = px.bar(
            topic_counts, x='count', y='chart_aspect', orientation='h',
            height=max(240, len(topic_counts) * 54 + 56),
            hover_data={'chart_aspect': False, 'aspect': True},
            labels={'aspect': 'Policy aspect', 'count': 'Entries'},
        )
        fig.update_yaxes(title_text=None, categoryorder='total ascending')
        show_chart(fig)
    with c2:
        st.subheader('Emotional tone')
        show_chart(px.scatter(
            f, x='valence', y='arousal', color='stakeholder_group',
            hover_data=['master_id', 'policy_aspect', 'macro_stance'], opacity=.65, height=420,
        ))
    st.info('Percentages describe entries in the filtered corpus, not percentages of U.S. teachers, students, or parents.')
with evidence:
    st.subheader('Searchable source evidence')
    st.caption('Some source URLs or excerpts may be synthetic or adapted. Do not present them as verified quotations without checking provenance.')
    show_cols = [
        'master_id', 'date', 'source_modality', 'stakeholder_group', 'policy_aspect',
        'macro_stance', 'primary_emotion', 'valence', 'arousal', 'summary_or_quote',
        'key_context_or_rationale', 'source_url',
    ]
    sorted_evidence = f[show_cols].sort_values('date', ascending=False)
    with st.expander('Read one entry at a time'):
        entries = sorted_evidence.set_index('master_id')
        entry_id = st.selectbox('Evidence entry', entries.index)
        entry = entries.loc[entry_id]
        st.write(entry['policy_aspect'])
        st.caption(f"{entry['stakeholder_group']} · {entry['macro_stance']}")
        st.write(entry['summary_or_quote'])
        st.write(entry['key_context_or_rationale'])
        if pd.notna(entry['source_url']):
            st.link_button('Open source', entry['source_url'])
    st.dataframe(sorted_evidence,use_container_width=True,hide_index=True,column_config={'source_url':st.column_config.LinkColumn('Source URL')})
    st.download_button('Export filtered entries (CSV)',f[show_cols].to_csv(index=False).encode('utf-8'),'filtered_evidence.csv','text/csv')
with policy:
    st.subheader('Draft policy provision explorer')
    st.caption('These are proposed examples, not findings or validated preferences of the sampled stakeholders.')
    proposals={
        'Academic integrity': 'Assignments should state permitted AI uses and disclosure requirements.',
        'Student data privacy': 'District-approved AI tools must undergo privacy and security review before use with student data.',
        'AI literacy': 'Students should receive age-appropriate instruction on AI limitations, bias, and verification.',
        'Fairness in enforcement': 'AI-detector output alone must not establish academic misconduct.',
        'Equitable access': 'Schools should provide equitable access to approved learning tools and alternatives.'
    }
    chosen=st.multiselect('Select provisions to include in a draft',list(proposals))
    if chosen:
        draft='# Draft K–12 AI Policy Provisions\n\n'+'\n\n'.join(f'## {name}\n{proposals[name]}' for name in chosen)
        st.markdown(draft)
        st.download_button('Download selected draft (Markdown)',draft,'draft_policy.md','text/markdown')
    st.warning('Before connecting proposals to evidence, add human-reviewed topic/request coding and document counterarguments and uncertainty.')
with methods:
    st.markdown('''### What this app measures
- **Macro stance** is the broad position assigned to an entry in the dataset. An entry can express ideas that fit more than one stance. See Overview for all nine definitions.
- **Valence** measures emotional tone, from negative (−1) through neutral (0) to positive (+1).
- **Arousal** measures emotional intensity, from low (0) to high (1).
- **Policy aspects**: labels already in the CSV, not a new independent topic model.

### Important limitations
- The corpus is not a probability sample of U.S. public opinion.
- Multiple entries may come from the same speaker, event, or thread.
- Check summaries and quotes against their original sources before citing them.
- Check the quality and consistency of stakeholder, stance, and emotion labels.
- A topic mention does not establish support for a specific policy.
''')
