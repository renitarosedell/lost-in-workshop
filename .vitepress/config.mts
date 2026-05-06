import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Lost in Raleigh',
  description: 'A hands-on AI agent workshop — MCP, A2A, multi-agent orchestration, and Azure AI Foundry',

  // Source is the repo root; .vitepress/ itself is excluded automatically
  srcDir: '.',
  srcExclude: [
    'node_modules/**',
    'spec/**',
    'specs/**',
    'create-agent/**',
    'facilitators/**',
    '.github/**',
    '.vscode/**',
    '.specify/**',
    '.claude/**',
    'README.md',
  ],

  // Required for GitHub Pages — set to your repo name
  base: '/lost-in-workshop/',

  lastUpdated: true,

  // localhost URLs appear intentionally in workshop code examples
  ignoreDeadLinks: [/^http:\/\/localhost/],

  themeConfig: {
    nav: [
      { text: 'Get started', link: '/' },
      { text: 'Get Azure', link: '/workshop/get-azure' },
      { text: 'Event Resources', link: '/workshop/event-resources' },
      {
        text: 'Workshop',
        items: [
          { text: 'Developer Environment Setup', link: '/workshop/dev-setup' },
          { text: '1. Connect to Azure OpenAI', link: '/workshop/step1' },
          { text: '2. Hello Raleigh', link: '/workshop/step2' },
          { text: '3. MCP Game Server', link: '/workshop/step3' },
          { text: '4. Memory', link: '/workshop/step4' },
          { text: '5. A2A Transport Expert', link: '/workshop/step5' },
          { text: '6. Multi-turn Conversations', link: '/workshop/step6' },
          { text: '7. Orchestration', link: '/workshop/step7' },
          { text: '8. Complete the Quest', link: '/workshop/step8' },
        ],
      },
      { text: 'Bonus', link: '/workshop/bonus-exercises' },
      {
        text: 'Facilitators',
        items: [
          { text: 'Pre-Event Checklist', link: '/workshop/pre-event-checklist' },
          { text: 'Deployment Guide', link: '/workshop/deployment-guide' },
          { text: 'Instructor Guide', link: '/workshop/instructor-guide' },
        ],
      },
    ],

    sidebar: {
      '/workshop/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Get Azure Subscription', link: '/workshop/get-azure' },
            { text: 'Developer Environment Setup', link: '/workshop/dev-setup' },
            { text: 'Azure AI Foundry Setup', link: '/workshop/azure-foundry-setup' },
            { text: 'Event Resources', link: '/workshop/event-resources' },
          ],
        },
        {
          text: 'Workshop Steps',
          items: [
            { text: '1. Connect to Azure OpenAI', link: '/workshop/step1' },
            { text: '2. Hello Raleigh', link: '/workshop/step2' },
            { text: '3. MCP Game Server', link: '/workshop/step3' },
            { text: '4. Memory', link: '/workshop/step4' },
            { text: '5. A2A Transport Expert', link: '/workshop/step5' },
            { text: '6. Multi-turn Conversations', link: '/workshop/step6' },
            { text: '7. Orchestration', link: '/workshop/step7' },
            { text: '8. Complete the Quest', link: '/workshop/step8' },
          ],
        },
        {
          text: 'Extras',
          items: [
            { text: 'Bonus Exercises', link: '/workshop/bonus-exercises' },
          ],
        },
        {
          text: 'Facilitators',
          collapsed: true,
          items: [
            { text: 'Pre-Event Checklist', link: '/workshop/pre-event-checklist' },
            { text: 'Deployment Guide', link: '/workshop/deployment-guide' },
            { text: 'Instructor Guide', link: '/workshop/instructor-guide' },
          ],
        },
      ],

      '/city-guide/': [
        {
          text: 'Raleigh City Guide',
          items: [
            { text: '1. Welcome to Raleigh', link: '/city-guide/raleigh/01_welcome_to_raleigh' },
            { text: '2. Downtown & Moore Square', link: '/city-guide/raleigh/02_downtown_and_moore_square' },
            { text: '3. Glenwood South', link: '/city-guide/raleigh/03_glenwood_south' },
            { text: '4. Five Points & Neighbourhood Character', link: '/city-guide/raleigh/04_five_points_and_neighbourhood_character' },
            { text: '5. Cameron Village & Midtown', link: '/city-guide/raleigh/05_cameron_village_and_midtown' },
            { text: '6. Warehouse District', link: '/city-guide/raleigh/06_warehouse_district' },
            { text: '7. Boylan Heights', link: '/city-guide/raleigh/07_boylan_heights' },
            { text: '8. North Hills', link: '/city-guide/raleigh/08_north_hills' },
            { text: '9. Getting Around: GoRaleigh Buses', link: '/city-guide/raleigh/09_getting_around_goRaleigh_buses' },
            { text: '10. Getting Around: GoTriangle & Regional Transit', link: '/city-guide/raleigh/10_getting_around_goTriangle_and_regional_transit' },
            { text: '11. Getting Around: Biking & Greenways', link: '/city-guide/raleigh/11_getting_around_biking_and_greenways' },
            { text: '12. Getting Around: Rideshare & Parking', link: '/city-guide/raleigh/12_getting_around_rideshare_and_parking' },
            { text: '13. Food & Drink', link: '/city-guide/raleigh/13_food_and_drink' },
            { text: '14. Arts & Culture', link: '/city-guide/raleigh/14_arts_and_culture' },
            { text: '15. Parks & Outdoors', link: '/city-guide/raleigh/15_parks_and_outdoors' },
            { text: '16. Research Triangle & Innovation', link: '/city-guide/raleigh/16_research_triangle_and_innovation' },
            { text: '17. History of Raleigh', link: '/city-guide/raleigh/17_history_of_raleigh' },
            { text: '18. Annual Events & Festivals', link: '/city-guide/raleigh/18_annual_events_and_festivals' },
            { text: '19. Practical Information', link: '/city-guide/raleigh/19_practical_information' },
            { text: '20. NC Biotech Center & RTP', link: '/city-guide/raleigh/20_nc_biotech_center_and_rtp' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/RoelantD/lost-in-workshop' },
    ],

    search: {
      provider: 'local',
    },

    footer: {
      message: 'Lost in Raleigh — AI Agent Workshop',
      copyright: 'Global AI Community',
    },
  },
})

