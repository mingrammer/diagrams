/**
 * Copyright (c) 2017-present, Facebook, Inc.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

const React = require('react');

const CompLibrary = require('../../core/CompLibrary.js');

const MarkdownBlock = CompLibrary.MarkdownBlock; /* Used to read markdown */
const Container = CompLibrary.Container;
const GridBlock = CompLibrary.GridBlock;

class HomeSplash extends React.Component {
  render() {
    const {siteConfig, language = ''} = this.props;
    const {baseUrl, docsUrl} = siteConfig;
    const docsPart = `${docsUrl ? `${docsUrl}/` : ''}`;
    const langPart = `${language ? `${language}/` : ''}`;
    const docUrl = doc => `${baseUrl}${docsPart}${langPart}${doc}`;

    const SplashContainer = props => (
      <div className="homeContainer">
        <div className="homeSplashFade">
          <div className="wrapper homeWrapper">{props.children}</div>
        </div>
      </div>
    );

    const Logo = props => (
      <div className="projectLogo">
        <img src={props.img_src} alt="Project Logo" />
      </div>
    );

    const ProjectTitle = props => (
      <h2 className="projectTitle">
        {props.title}
        <small>{props.tagline}</small>
      </h2>
    );

    const PromoSection = props => (
      <div className="section promoSection">
        <div className="promoRow">
          <div className="pluginRowBlock">{props.children}</div>
        </div>
      </div>
    );

    const Button = props => (
      <div className="pluginWrapper buttonWrapper">
        <a className="button" href={props.href} target={props.target}>
          {props.children}
        </a>
      </div>
    );

    return (
      <SplashContainer>
        <Logo img_src={`${baseUrl}img/diagrams.png`} />
        <div className="inner">
          <ProjectTitle tagline={siteConfig.tagline} title={siteConfig.title} />
          <PromoSection>
            <Button href={docUrl('getting-started/installation')}>Try It Out</Button>
            <Button href={docUrl('getting-started/examples')}>Show Examples</Button>
          </PromoSection>
        </div>
      </SplashContainer>
    );
  }
}

class Index extends React.Component {
  render() {
    const {config: siteConfig, language = ''} = this.props;
    const {baseUrl} = siteConfig;

    const Block = props => (
      <Container
        padding={['bottom', 'top']}
        id={props.id}
        background={props.background}>
        <GridBlock
          align="center"
          contents={props.children}
          layout={props.layout}
        />
      </Container>
    );

    const About = () => (
      <div
        className="productShowcaseSection paddingBottom"
        style={{textAlign: 'center'}}>
        <h2>About Diagrams</h2>
        <MarkdownBlock>
            Diagrams lets you draw the cloud system architecture **in Python code**.
        </MarkdownBlock>
        <MarkdownBlock>
            It was born for **prototyping** a new system architecture without any design tools. You can also describe or visualize the existing system architecture as well.
        </MarkdownBlock>
        <MarkdownBlock>
            `Diagram as Code` allows you to **track** the architecture diagram changes in any **version control** system.
        </MarkdownBlock>
        <MarkdownBlock>
            Diagrams currently supports main major providers including: `AWS`, `Azure`, `GCP`, `Kubernetes`, `Alibaba Cloud`, `Oracle Cloud` etc... It also supports `On-Premise` nodes, `SaaS` and major `Programming` frameworks and languages.
        </MarkdownBlock>
        <MarkdownBlock>
            `NOTE: It does not control any actual cloud resources nor does it generate cloud formation or terraform code. It is just for drawing the cloud system architecture diagrams.`
        </MarkdownBlock>
      </div>
    );

    const Example = () => (
      <Block>
        {[
          {
            image: `${baseUrl}img/message_collecting_code.png`,
            imageAlign: 'left',
          },
          {
            image: `${baseUrl}img/message_collecting_diagram.png`,
            imageAlign: 'right',
          },
        ]}
      </Block>
    );

    const Example2 = () => (
      <Block>
        {[
          {
            image: `${baseUrl}img/event_processing_code.png`,
              imageAlign: 'left',
          },
          {
            image: `${baseUrl}img/event_processing_diagram.png`,
              imageAlign: 'right',
          },
        ]}
      </Block>
    );

    return (
      <div>
        <HomeSplash siteConfig={siteConfig} language={language} />
        <div className="mainContainer">
          <About />
          <Example />
          <Example2 />
        </div>
      </div>
    );
  }
}

module.exports = Index;
