/**
 * Copyright (c) 2017-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

// See https://docusaurus.io/docs/site-config for all the possible
// site configuration options.

const siteConfig = {
  title: 'Diagrams',
  tagline: 'Diagram as Code',
  url: 'https://diagrams.mingrammer.com',
  baseUrl: '/',
  cname: 'diagrams.mingrammer.com',
  projectName: 'diagrams',
  organizationName: 'mingrammer',

  headerLinks: [
    {doc: 'getting-started/installation', label: 'Docs'},
    {doc: 'guides/diagram', label: 'Guides'},
    {doc: 'nodes/aws', label: 'Nodes'},
    {href: 'https://github.com/mingrammer/diagrams', label: 'GitHub'},
    {href: 'https://www.buymeacoffee.com/mingrammer', label: 'Sponsoring'},
  ],

  headerIcon: 'img/diagrams.ico',
  footerIcon: 'img/diagrams.ico',
  favicon: 'img/diagrams.ico',

  colors: {
    primaryColor: '#5E73E5',
    secondaryColor: '#5E89E5',
  },

  copyright: `Copyright © ${new Date().getFullYear()} mingrammer`,

  highlight: {
    // Highlight.js theme to use for syntax highlighting in code blocks.
    theme: 'default',
  },

  // Add custom scripts here that would be placed in <script> tags.
  scripts: ['https://buttons.github.io/buttons.js'],

  // On page navigation for the current documentation page.
  onPageNav: 'separate',
  cleanUrl: true,

  // Open Graph and Twitter card images.
  facebookComments: false,
  twitterImage: 'img/diagrams.png',
  ogImage: 'img/diagrams.png',

  docsSideNavCollapsible: false,

  enableUpdateTime: true,

  gaTrackingId: 'UA-84081627-3',
};

module.exports = siteConfig;
