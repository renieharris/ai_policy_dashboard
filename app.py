from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='K–12 AI Policy Evidence Lab', layout='wide')
st.title('K–12 AI Policy Evidence Lab')
st.caption('Exploratory dashboard covering video sources, community discourse, and public hearings. Verify source provenance before publishing findings.')

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
selected_stances = st.sidebar.multiselect('Macro stance', sorted(df['macro_stance'].dropna().unique()))
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
    counts = f.groupby(['stakeholder_group', 'macro_stance']).size().reset_index(name='count')
    counts['share'] = counts['count'] / counts.groupby('stakeholder_group')['count'].transform('sum')
    fig = px.bar(counts, x='stakeholder_group', y='share', color='macro_stance', barmode='stack', hover_data=['count'], labels={'share':'Share of entries', 'stakeholder_group':'Stakeholder'})
    fig.update_yaxes(tickformat='.0%')
    st.plotly_chart(fig, use_container_width=True)
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Policy aspects mentioned')
        topic_counts=f['policy_aspect'].value_counts().head(15).reset_index()
        topic_counts.columns=['aspect','count']
        st.plotly_chart(px.bar(topic_counts, x='count', y='aspect', orientation='h', labels={'aspect':'Policy aspect'}).update_layout(yaxis={'categoryorder':'total ascending'}),use_container_width=True)
    with c2:
        st.subheader('Emotional tone')
        st.plotly_chart(px.scatter(f,x='valence',y='arousal',color='stakeholder_group',hover_data=['master_id','policy_aspect','macro_stance'],opacity=.65),use_container_width=True)
    st.info('Percentages describe entries in the filtered corpus, not percentages of U.S. teachers, students, or parents.')
with evidence:
    st.subheader('Searchable source evidence')
    st.caption('Some source URLs or excerpts may be synthetic or adapted. Do not present them as verified quotations without checking provenance.')
    show_cols = [
        'master_id', 'date', 'source_modality', 'stakeholder_group', 'policy_aspect',
        'macro_stance', 'primary_emotion', 'valence', 'arousal', 'summary_or_quote',
        'key_context_or_rationale', 'source_url',
    ]
    st.dataframe(f[show_cols].sort_values('date',ascending=False),use_container_width=True,hide_index=True,column_config={'source_url':st.column_config.LinkColumn('Source URL')})
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
- **Macro stance**: preexisting categories in the supplied CSV; categories are not necessarily mutually exclusive in meaning.
- **Valence and arousal**: supplied numerical scores. Confirm their scale and NLP methodology before interpretation.
- **Policy aspects**: labels already in the CSV, not a new independent topic model.

### Important limitations
- The corpus is not a probability sample of U.S. public opinion.
- Multiple entries may come from the same speaker, event, or thread.
- Check summaries and quotes against their original sources before citing them.
- Check the quality and consistency of stakeholder, stance, and emotion labels.
- A topic mention does not establish support for a specific policy.
''')
