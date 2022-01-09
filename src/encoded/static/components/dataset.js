import React from 'react';
import PropTypes from 'prop-types';
import _ from 'underscore';
import { Panel, PanelBody } from '../libs/bootstrap/panel';
import DropdownButton from '../libs/bootstrap/button';
import { DropdownMenu } from '../libs/bootstrap/dropdown-menu';
import * as globals from './globals';
import { Breadcrumbs } from './navigation';
import { DbxrefList } from './dbxref';
import { FetchedItems } from './fetched';
import { auditDecor } from './audit';
import StatusLabel from './statuslabel';
import pubReferenceList from './reference';
import { donorDiversity, publicDataset, AlternateAccession } from './objectutils';
import { softwareVersionList } from './software';
import { SortTablePanel, SortTable } from './sorttable';
import { ProjectBadge } from './image';
import { DocumentsPanelReq } from './doc';
import { FileGallery, DatasetFiles } from './filegallery';
import { AwardRef } from './typeutils';

// Return a summary of the given biosamples, ready to be displayed in a React component.
export function annotationBiosampleSummary(annotation) {
    const organismName = (annotation.organism && annotation.organism.scientific_name) ? <i>{annotation.organism.scientific_name}</i> : null;
    const lifeStageString = (annotation.relevant_life_stage && annotation.relevant_life_stage !== 'unknown') ? <span>{annotation.relevant_life_stage}</span> : null;
    const timepointString = annotation.relevant_timepoint ? <span>{annotation.relevant_timepoint + (annotation.relevant_timepoint_units ? ` ${annotation.relevant_timepoint_units}` : '')}</span> : null;

    // Build an array of strings we can join, not including empty strings
    const summaryStrings = _.compact([organismName, lifeStageString, timepointString]);

    if (summaryStrings.length) {
        return (
            <span className="biosample-summary">
                {summaryStrings.map((summaryString, i) =>
                    <span key={i}>
                        {i > 0 ? <span>{', '}{summaryString}</span> : <span>{summaryString}</span>}
                    </span>,
                )}
            </span>
        );
    }
    return null;
}

export function embeddingBiosampleSummary(embedding) {
    const organismName = (embedding.organism && embedding.organism.scientific_name) ? <i>{embedding.organism.scientific_name}</i> : null;
    const lifeStageString = (embedding.relevant_life_stage && embedding.relevant_life_stage !== 'unknown') ? <span>{embedding.relevant_life_stage}</span> : null;
    const timepointString = embedding.relevant_timepoint ? <span>{embedding.relevant_timepoint + (embedding.relevant_timepoint_units ? ` ${embedding.relevant_timepoint_units}` : '')}</span> : null;

    // Build an array of strings we can join, not including empty strings
    const summaryStrings = _.compact([organismName, lifeStageString, timepointString]);

    if (summaryStrings.length) {
        return (
            <span className="biosample-summary">
                {summaryStrings.map((summaryString, i) =>
                    <span key={i}>
                        {i > 0 ? <span>{', '}{summaryString}</span> : <span>{summaryString}</span>}
                    </span>,
                )}
            </span>
        );
    }
    return null;
}

export function modelBiosampleSummary(model) {
    const organismName = (model.organism && model.organism.scientific_name) ? <i>{model.organism.scientific_name}</i> : null;
    const lifeStageString = (model.relevant_life_stage && model.relevant_life_stage !== 'unknown') ? <span>{model.relevant_life_stage}</span> : null;
    const timepointString = model.relevant_timepoint ? <span>{model.relevant_timepoint + (model.relevant_timepoint_units ? ` ${model.relevant_timepoint_units}` : '')}</span> : null;

    // Build an array of strings we can join, not including empty strings
    const summaryStrings = _.compact([organismName, lifeStageString, timepointString]);

    if (summaryStrings.length) {
        return (
            <span className="biosample-summary">
                {summaryStrings.map((summaryString, i) =>
                    <span key={i}>
                        {i > 0 ? <span>{', '}{summaryString}</span> : <span>{summaryString}</span>}
                    </span>,
                )}
            </span>
        );
    }
    return null;
}
export function perturbationBiosampleSummary(perturbation) {
    const organismName = (perturbation.organism && perturbation.organism.scientific_name) ? <i>{perturbation.organism.scientific_name}</i> : null;
    const lifeStageString = (perturbation.relevant_life_stage && perturbation.relevant_life_stage !== 'unknown') ? <span>{perturbation.relevant_life_stage}</span> : null;
    const timepointString = perturbation.relevant_timepoint ? <span>{perturbation.relevant_timepoint + (perturbation.relevant_timepoint_units ? ` ${perturbation.relevant_timepoint_units}` : '')}</span> : null;

    // Build an array of strings we can join, not including empty strings
    const summaryStrings = _.compact([organismName, lifeStageString, timepointString]);

    if (summaryStrings.length) {
        return (
            <span className="biosample-summary">
                {summaryStrings.map((summaryString, i) =>
                    <span key={i}>
                        {i > 0 ? <span>{', '}{summaryString}</span> : <span>{summaryString}</span>}
                    </span>,
                )}
            </span>
        );
    }
    return null;
}


// Break the given camel-cased name into space-separated words just before the interior capital letters.
function breakSetName(name) {
    return name.replace(/(\S)([A-Z])/g, '$1 $2');
}


// Display Annotation page, a subtype of Dataset.
class AnnotationComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);

        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Make a biosample summary string
        const biosampleSummary = annotationBiosampleSummary(context);

        // Determine this experiment's ENCODE version
        const encodevers = globals.encodeVersion(context);

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Make array of superseded_by accessions
        let supersededBys = [];
        if (context.superseded_by && context.superseded_by.length) {
            supersededBys = context.superseded_by.map(supersededBy => globals.atIdToAccession(supersededBy));
        }

        // Make array of supersedes accessions
        let supersedes = [];
        if (context.supersedes && context.supersedes.length) {
            supersedes = context.supersedes.map(supersede => globals.atIdToAccession(supersede));
        }

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for annotation file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        {supersededBys.length ? <h4 className="superseded-acc">Superseded by {supersededBys.join(', ')}</h4> : null}
                        {supersedes.length ? <h4 className="superseded-acc">Supersedes {supersedes.join(', ')}</h4> : null}
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'annotation-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'annotation-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_term_name || biosampleSummary ?
                                        <div data-test="biosample">
                                            <dt>Biosample summary</dt>
                                            <dd>
                                                {context.biosample_term_name}
                                                {context.biosample_term_name ? <span>{' '}</span> : null}
                                                {biosampleSummary ? <span>({biosampleSummary})</span> : null}
                                            </dd>
                                        </div>
                                    : null}

                                    {context.biosample_type ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample type</dt>
                                            <dd>{context.biosample_type}</dd>
                                        </div>
                                    : null}

                                    {context.organism ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{context.organism.name}</dd>
                                        </div>
                                    : null}

                                    {context.annotation_type ?
                                        <div data-test="type">
                                            <dt>Annotation type</dt>
                                            <dd className="sentence-case">{context.annotation_type}</dd>
                                        </div>
                                    : null}
                                    {context.annotation_type_category ?
                                        <div data-test="type">
                                            <dt>Underlying assay</dt>
                                            <dd className="sentence-case">{context.annotation_type_category.map(function(item){ return <div className="item">{item}</div>; })}</dd>
                                        </div>
                                    : null}
                                    {context.target ?
                                        <div data-test="target">
                                            <dt>Target</dt>
                                            <dd><a href={context.target['@id']}>{context.target.label}</a></dd>
                                        </div>
				     : null}
		             {context.annotation_pipeline && context.annotation_pipeline.length ?
			      <div data-test="pipelineused">
                                <dt>Pipeline used</dt>
		                {context.annotation_pipeline.map((annotation_pipeline, i) => (
		                <span key={i}>
			        {i > 0 ? ', ' : ''}
		                <dd><a href={annotation_pipeline['@id']}>{annotation_pipeline.accession}</a></dd>
			        </span>
			       ))}
                             </div>
		             : null}
                                
                                    {context.software_used && context.software_used.length ?
                                        <div data-test="softwareused">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                           
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.encyclopedia_version ?
                                        <div data-test="encyclopediaversion">
                                            <dt>Encyclopedia version</dt>
                                            <dd>{context.encyclopedia_version}</dd>
                                        </div>
                                    : null}

                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    <div data-test="collectiontags">
                                        <dt>Collection Tags</dt>
                                        <dd>
                                            {context.collection_tags && context.collection_tags ?
                                                <DbxrefList context={context} dbxrefs={context.collection_tags} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>

                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={encodevers} />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

AnnotationComponent.propTypes = {
    context: PropTypes.object, // Annotation being displayed
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

AnnotationComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const Annotation = auditDecor(AnnotationComponent);

globals.contentViews.register(Annotation, 'Annotation');
// Display Embeddings page, a subtype of Dataset.
class EmbeddingComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);

        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Make a biosample summary string
        const biosampleSummary = embeddingBiosampleSummary(context);

        // Determine this experiment's ENCODE version
        const encodevers = globals.encodeVersion(context);

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Make array of superseded_by accessions
        let supersededBys = [];
        if (context.superseded_by && context.superseded_by.length) {
            supersededBys = context.superseded_by.map(supersededBy => globals.atIdToAccession(supersededBy));
        }

        // Make array of supersedes accessions
        let supersedes = [];
        if (context.supersedes && context.supersedes.length) {
            supersedes = context.supersedes.map(supersede => globals.atIdToAccession(supersede));
        }

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for embeddings file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        {supersededBys.length ? <h4 className="superseded-acc">Superseded by {supersededBys.join(', ')}</h4> : null}
                        {supersedes.length ? <h4 className="superseded-acc">Supersedes {supersedes.join(', ')}</h4> : null}
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'embedding-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'embedding-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_term_name || biosampleSummary ?
                                        <div data-test="biosample">
                                            <dt>Biosample summary</dt>
                                            <dd>
                                                <DbxrefList context={context.biosample_term_name} dbxrefs={context.biosample_term_name} />
                                                {context.biosample_term_name ? <span>{' '}</span> : null}
                                                {biosampleSummary ? <span>({biosampleSummary})</span> : null}
                                            </dd>
                                        </div>
                                    : null}

                                    {context.biosample_type ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample type</dt>
                                            <dd><DbxrefList context={context.biosample_type} dbxrefs={context.biosample_type} /></dd>
                                        </div>
                                    : null}
                                    {context.organism ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{context.organism.name}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_type ?
                                        <div data-test="type">
                                            <dt>Type</dt>
                                            <dd className="sentence-case">{context.embeddings_type}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_underlying_assay ?
                                        <div data-test="type">
                                            <dt>Underlying Assay</dt>
                                            <dd className="sentence-case">{context.embeddings_underlying_assay}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_type_category ?
                                        <div data-test="type">
                                            <dt>Underlying assay</dt>
                                            <dd className="sentence-case">{context.embeddings_type_category.map(function(item){ return <div className="item">{item}</div>; })}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_category ?
                                        <div data-test="type">
                                            <dt>Category</dt>
                                            <dd className="sentence-case">{context.embeddings_category}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_source ?
                                        <div data-test="type">
                                            <dt>Source</dt>
                                            <dd className="sentence-case">{context.embeddings_source}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_pipeline ?
                                        <div data-test="type">
                                            <dt>Pipeline</dt>
                                            <dd className="sentence-case">{context.embeddings_pipeline}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_unit ?
                                        <div data-test="type">
                                            <dt>Unit</dt>
                                            <dd className="sentence-case">{context.embeddings_unit}</dd>
                                        </div>
                                    : null}
                                    {context.embeddings_cells ?
                                        <div data-test="type">
                                            <dt>Number of Cells</dt>
                                            <dd className="sentence-case">{context.embeddings_cells}</dd>
                                        </div>
                                    : null}
                                    {context.target ?
                                        <div data-test="target">
                                            <dt>Target</dt>
                                            <dd><a href={context.target['@id']}>{context.target.label}</a></dd>
                                        </div>
                                    : null}

                                    {context.software_used && context.software_used.length ?
                                        <div data-test="softwareused">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.encyclopedia_version ?
                                        <div data-test="encyclopediaversion">
                                            <dt>Encyclopedia version</dt>
                                            <dd>{context.encyclopedia_version}</dd>
                                        </div>
                                    : null}

                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    <div data-test="collectiontags">
                                        <dt>Collection Tags</dt>
                                        <dd>
                                            {context.collection_tags && context.collection_tags ?
                                                <DbxrefList context={context} dbxrefs={context.collection_tags} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>
		             {context.datasets_annotation && context.datasets_annotation.length ?
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-12">
                            <div style={{marginLeft: '2rem', marginRight: '2rem'}}>
                                		 <div data-test="datasets">
                                <h4>Annotations</h4>
		 <dd>
		 {context.datasets_annotation.map((annotation, i) => (
		     <span key={i}>
			 {i > 0 ? ', ' : ''}
		         <a href={annotation['@id']}>{annotation.accession}</a>
			 </span>
			 ))}
		 </dd>
                 </div>
		 </div>
	        </div>
                </div>
                </PanelBody>
                </Panel> 
		 : null}
	             {context.datasets_experiment && context.datasets_experiment.length ?
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-12">
                            <div style={{marginLeft: '2rem', marginRight: '2rem'}}>
	
                                		 <div data-test="assay">
                                <h4>Assays</h4>
		 <dd>
		 {context.datasets_experiment.map((dataset, i) => (
		     <span key={i}>
			 {i > 0 ? ', ' : ''}
		         <a href={dataset['@id']}>{dataset.accession}</a>
			 </span>
			 ))}
		 </dd>
                 </div>
		 </div>
	        </div>
                </div>
                </PanelBody>
                </Panel> 
		 : null}
                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={encodevers} />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

EmbeddingComponent.propTypes = {
    context: PropTypes.object, // Embeddings being displayed
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

EmbeddingComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const Embedding = auditDecor(EmbeddingComponent);

globals.contentViews.register(Embedding, 'Embedding');

// Display perturbation page, a subtype of Dataset.
class PerturbationComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);

        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Make a biosample summary string
        const biosampleSummary = perturbationBiosampleSummary(context);

        // Determine this experiment's ENCODE version
        const encodevers = globals.encodeVersion(context);

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Make array of superseded_by accessions
        let supersededBys = [];
        if (context.superseded_by && context.superseded_by.length) {
            supersededBys = context.superseded_by.map(supersededBy => globals.atIdToAccession(supersededBy));
        }

        // Make array of supersedes accessions
        let supersedes = [];
        if (context.supersedes && context.supersedes.length) {
            supersedes = context.supersedes.map(supersede => globals.atIdToAccession(supersede));
        }

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for gene perturbation file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        {supersededBys.length ? <h4 className="superseded-acc">Superseded by {supersededBys.join(', ')}</h4> : null}
                        {supersedes.length ? <h4 className="superseded-acc">Supersedes {supersedes.join(', ')}</h4> : null}
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'perturbation-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'perturbation-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_term_name || biosampleSummary ?
                                        <div data-test="biosample">
                                            <dt>Biosample summary</dt>
                                            <dd>
                                                <DbxrefList context={context.biosample_term_name} dbxrefs={context.biosample_term_name} />
                                                {context.biosample_term_name ? <span>{' '}</span> : null}
                                                {biosampleSummary ? <span>({biosampleSummary})</span> : null}
                                            </dd>
                                        </div>
                                    : null}

                                    {context.biosample_type ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample type</dt>
                                            <dd><DbxrefList context={context.biosample_type} dbxrefs={context.biosample_type} /></dd>
                                        </div>
                                    : null}
                                    {context.biosample_conditions ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample Conditions</dt>
                                            <dd><DbxrefList context={context.biosample_conditions} dbxrefs={context.biosample_conditions} /></dd>
                                        </div>
                                    : null}
                                    {context.phenotypes_measured ?
                                        <div data-test="biosampletype">
                                            <dt>Phenotypes Measured</dt>
                                            <dd><DbxrefList context={context.phenotypes_measured} dbxrefs={context.phenotypes_measured} /></dd>
                                        </div>
                                    : null}
                                    {context.organism ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{context.organism.name}</dd>
                                        </div>
                                    : null}
                                    {context.modification_type ?
                                        <div data-test="type">
                                            <dt>Modification type</dt>
                                            <dd className="sentence-case">{context.modification_type}</dd>
                                        </div>
                                    : null}
                                    {context.assay_design ?
                                        <div data-test="type">
                                            <dt>Assay Design</dt>
                                            <dd className="sentence-case">{context.assay_design}</dd>
                                        </div>
                                    : null}
                                    {context.assay_readout ?
                                        <div data-test="type">
                                            <dt>Assay Readout</dt>
                                            <dd className="sentence-case">{context.assay_readout}</dd>
                                        </div>
                                    : null}
                                    {context.target ?
                                        <div data-test="target">
                                            <dt>Target</dt>
                                            <dd><a href={context.target['@id']}>{context.target.label}</a></dd>
                                        </div>
                                    : null}
                                    {context.pooled_design ?
                                        <div data-test="type">
                                            <dt>Pooled Design</dt>
                                            <dd className="sentence-case">{context.pooled_design}</dd>
                                        </div>
                                    : null}
                                    {context.library ?
                                        <div data-test="type">
                                            <dt>Library</dt>
                                            <dd className="sentence-case">{context.library}</dd>
                                        </div>
                                    : null}
                                    {context.gating_strategy ?
                                        <div data-test="type">
                                            <dt>Gating Strategy</dt>
                                            <dd className="sentence-case">{context.gating_strategy}</dd>
                                        </div>
                                    : null}
                                    {context.partitioning_strategy ?
                                        <div data-test="type">
                                            <dt>Partitioning Strategy</dt>
                                            <dd className="sentence-case">{context.partitioning_strategy}</dd>
                                        </div>
                                    : null}
                                    {context.source_rna ?
                                        <div data-test="type">
                                            <dt>Source of siRNA/shRNA</dt>
                                            <dd className="sentence-case">{context.source_rna}</dd>
                                        </div>
                                    : null}
                                    {context.commerical_assay ?
                                        <div data-test="type">
                                            <dt>Commerical Assays</dt>
                                            <dd className="sentence-case">{context.commerical_assay}</dd>
                                        </div>
                                    : null}
                                    {context.target ?
                                        <div data-test="target">
                                            <dt>Target</dt>
                                            <dd><a href={context.target['@id']}>{context.target.label}</a></dd>
                                        </div>
                                    : null}
                                    {context.software_used && context.software_used.length ?
                                        <div data-test="softwareused">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.encyclopedia_version ?
                                        <div data-test="encyclopediaversion">
                                            <dt>Encyclopedia version</dt>
                                            <dd>{context.encyclopedia_version}</dd>
                                        </div>
                                    : null}

                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    <div data-test="collectiontags">
                                        <dt>Collection Tags</dt>
                                        <dd>
                                            {context.collection_tags && context.collection_tags ?
                                                <DbxrefList context={context} dbxrefs={context.collection_tags} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>
                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={encodevers} />
		 <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

PerturbationComponent.propTypes = {
    context: PropTypes.object, //Perturbation being displayed
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

PerturbationComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const Perturbation = auditDecor(PerturbationComponent);

globals.contentViews.register(Perturbation, 'Perturbation');

// Display model page, a subtype of Dataset.
class ModelComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);

        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Make a biosample summary string
        const biosampleSummary = modelBiosampleSummary(context);

        // Determine this experiment's ENCODE version
        const encodevers = globals.encodeVersion(context);

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Make array of superseded_by accessions
        let supersededBys = [];
        if (context.superseded_by && context.superseded_by.length) {
            supersededBys = context.superseded_by.map(supersededBy => globals.atIdToAccession(supersededBy));
        }

        // Make array of supersedes accessions
        let supersedes = [];
        if (context.supersedes && context.supersedes.length) {
            supersedes = context.supersedes.map(supersede => globals.atIdToAccession(supersede));
        }

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for statistical model file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        {supersededBys.length ? <h4 className="superseded-acc">Superseded by {supersededBys.join(', ')}</h4> : null}
                        {supersedes.length ? <h4 className="superseded-acc">Supersedes {supersedes.join(', ')}</h4> : null}
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'perturbation-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'model-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>
                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}
                                    {context.model_biosamples ?
                                        <div data-test="description">
                                            <dt>Biosamples</dt>
                                            <dd>{context.model_biosamples}</dd>
                                        </div>
                                    : null}
                                    {context.biosample_type ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample type</dt>
                                            <dd><DbxrefList context={context.biosample_type} dbxrefs={context.biosample_type} /></dd>
                                        </div>
                                    : null}
                                    {context.organism ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{context.organism.name}</dd>
                                        </div>
                                    : null}
                                    {context.model_name ?
                                        <div data-test="type">
                                            <dt>Name</dt>
                                            <dd className="sentence-case">{context.model_name}</dd>
                                        </div>
                                    : null}
                                    {context.model_type ?
                                        <div data-test="type">
                                            <dt>Type</dt>
                                            <dd className="sentence-case">{context.model_type}</dd>
                                        </div>
                                    : null}
                                    {context.model_underlying_assay ?
                                        <div data-test="type">
                                            <dt>Underlying assay for statistical model</dt>
                                            <dd className="sentence-case">{context.model_underlying_assay}</dd>
                                        </div>
                                    : null}
                                    {context.model_input_format ?
                                        <div data-test="type">
                                            <dt>Input</dt>
                                            <dd className="sentence-case">{context.model_input_format}</dd>
                                        </div>
                                    : null}
                                    {context.model_output ?
                                        <div data-test="type">
                                            <dt>Output</dt>
                                            <dd className="sentence-case">{context.model_output}</dd>
                                        </div>
                                    : null}
                                    {context.model_format ?
                                        <div data-test="type">
                                            <dt>Format</dt>
                                            <dd className="sentence-case">{context.model_format}</dd>
                                        </div>
                                    : null}
                                    {context.model_training ?
                                        <div data-test="type">
                                            <dt>Training</dt>
                                            <dd className="sentence-case">{context.model_training}</dd>
                                        </div>
                                    : null}
                                    {context.model_validation ?
                                        <div data-test="type">
                                            <dt>Validation</dt>
                                            <dd className="sentence-case">{context.model_validation}</dd>
                                        </div>
                                    : null}
                                    {context.target ?
                                        <div data-test="target">
                                            <dt>Target</dt>
                                            <dd><a href={context.target['@id']}>{context.target.label}</a></dd>
                                        </div>
                                    : null}

                                    {context.software_used && context.software_used.length ?
                                        <div data-test="softwareused">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.encyclopedia_version ?
                                        <div data-test="encyclopediaversion">
                                            <dt>Encyclopedia version</dt>
                                            <dd>{context.encyclopedia_version}</dd>
                                        </div>
                                    : null}

                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    <div data-test="collectiontags">
                                        <dt>Collection Tags</dt>
                                        <dd>
                                            {context.collection_tags && context.collection_tags ?
                                                <DbxrefList context={context} dbxrefs={context.collection_tags} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>
                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>
		             {context.datasets_annotation && context.datasets_annotation.length ?
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-12">
                            <div style={{marginLeft: '2rem', marginRight: '2rem'}}>
                                		 <div data-test="annotation">
                                <h4>Annotations</h4>
		 <dd>
		 {context.datasets_annotation.map((dataset, i) => (
		     <span key={i}>
			 {i > 0 ? ', ' : ''}
		         <a href={dataset['@id']}>{dataset.accession}</a>
			 </span>
			 ))}
		 </dd>
                 </div>
		 </div>
	        </div>
                </div>
                </PanelBody>
                </Panel> 
		 : null}
		             {context.datasets_experiment && context.datasets_experiments.length ?
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-12">
                            <div style={{marginLeft: '2rem', marginRight: '2rem'}}>
                                		 <div data-test="assay">
                                <h4>Assays</h4>
		 <dd>
		 {context.datasets_experiment.map((dataset, i) => (
		     <span key={i}>
			 {i > 0 ? ', ' : ''}
		         <a href={dataset['@id']}>{dataset.accession}</a>
			 </span>
			 ))}
		 </dd>
                 </div>
		 </div>
	        </div>
                </div>
                </PanelBody>
                </Panel> 
		 : null}
                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={encodevers} />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

ModelComponent.propTypes = {
    context: PropTypes.object, //Perturbation being displayed
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

ModelComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const Model = auditDecor(ModelComponent);

globals.contentViews.register(Model, 'Model');

// Display Annotation page, a subtype of Dataset.
class PublicationDataComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);
        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Render the publication links
        const referenceList = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for publication file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'publicationdata-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'publicationdata-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    {context.assay_term_name && context.assay_term_name.length ?
                                        <div data-test="assaytermname">
                                            <dt>Assay(s)</dt>
                                            <dd>{context.assay_term_name.join(', ')}</dd>
                                        </div>
                                    : null}

                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_term_name && context.biosample_term_name.length ?
                                        <div data-test="biosampletermname">
                                            <dt>Biosample term name</dt>
                                            <dd>{context.biosample_term_name.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_type && context.biosample_type.length ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample type</dt>
                                            <dd>{context.biosample_type.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {context.dataset_type ?
                                        <div data-test="type">
                                            <dt>Dataset type</dt>
                                            <dd className="sentence-case">{context.dataset_type}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>

                                    {referenceList ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{referenceList}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>

                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={globals.encodeVersion(context)} hideGraph />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

PublicationDataComponent.propTypes = {
    context: PropTypes.object, // PublicationData object to display
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

PublicationDataComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const PublicationData = auditDecor(PublicationDataComponent);

globals.contentViews.register(PublicationData, 'PublicationData');


// Display Annotation page, a subtype of Dataset.
class ReferenceComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);
        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for reference file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'reference-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'reference-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.reference_type ?
                                        <div data-test="type">
                                            <dt>Reference type</dt>
                                            <dd>{context.reference_type}</dd>
                                        </div>
                                    : null}

                                    {context.organism ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{context.organism.name}</dd>
                                        </div>
                                    : null}

                                    {context.software_used && context.software_used.length ?
                                        <div data-test="softwareused">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>

                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>

                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={globals.encodeVersion(context)} hideGraph altFilterDefault />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

ReferenceComponent.propTypes = {
    context: PropTypes.object, // Reference object to display
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

ReferenceComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const Reference = auditDecor(ReferenceComponent);

globals.contentViews.register(Reference, 'Reference');


// Display Annotation page, a subtype of Dataset.
class ProjectComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);
        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Collect organisms
        const organisms = (context.organism && context.organism.length) ? _.uniq(context.organism.map(organism => organism.name)) : [];

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Get a list of reference links
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for project file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'project-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'project-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    {context.assay_term_name && context.assay_term_name.length ?
                                        <div data-test="assaytermname">
                                            <dt>Assay(s)</dt>
                                            <dd>{context.assay_term_name.join(', ')}</dd>
                                        </div>
                                    : null}

                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.project_type ?
                                        <div data-test="type">
                                            <dt>Project type</dt>
                                            <dd className="sentence-case">{context.project_type}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_term_name && context.biosample_term_name.length ?
                                        <div data-test="biosampletermname">
                                            <dt>Biosample term name</dt>
                                            <dd>{context.biosample_term_name.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {context.biosample_type && context.biosample_type.length ?
                                        <div data-test="biosampletype">
                                            <dt>Biosample type</dt>
                                            <dd>{context.biosample_type.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {organisms.length ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{organisms.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {context.software_used && context.software_used.length ?
                                        <div data-test="softwareused">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>

                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>

                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={globals.encodeVersion(context)} hideGraph />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

ProjectComponent.propTypes = {
    context: PropTypes.object, // Project object to display
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

ProjectComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const Project = auditDecor(ProjectComponent);

globals.contentViews.register(Project, 'Project');


// Display Annotation page, a subtype of Dataset.
class UcscBrowserCompositeComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);
        const statuses = [{ status: context.status, title: 'Status' }];

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Collect organisms
        const organisms = (context.organism && context.organism.length) ? _.uniq(context.organism.map(organism => organism.name)) : [];

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const filesetType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(filesetType), uri: `/search/?type=${filesetType}`, wholeTip: `Search for ${filesetType}` },
        ];

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for UCSC browser composite file set {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'ucscbrowsercomposite-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'ucscbrowsercomposite-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    {context.assay_term_name && context.assay_term_name.length ?
                                        <div data-test="assays">
                                            <dt>Assay(s)</dt>
                                            <dd>{context.assay_term_name.join(', ')}</dd>
                                        </div>
                                    : null}

                                    <div data-test="accession">
                                        <dt>Accession</dt>
                                        <dd>{context.accession}</dd>
                                    </div>

                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    {context.dataset_type ?
                                        <div data-test="type">
                                            <dt>Dataset type</dt>
                                            <dd className="sentence-case">{context.dataset_type}</dd>
                                        </div>
                                    : null}

                                    {organisms.length ?
                                        <div data-test="organism">
                                            <dt>Organism</dt>
                                            <dd>{organisms.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {context.software_used && context.software_used.length ?
                                        <div data-test="software-used">
                                            <dt>Software used</dt>
                                            <dd>{softwareVersionList(context.software_used)}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    {context.lab ?
                                        <div data-test="lab">
                                            <dt>Lab</dt>
                                            <dd>{context.lab.title}</dd>
                                        </div>
                                    : null}

                                    <AwardRef context={context} adminUser={adminUser} />

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd><DbxrefList context={context} dbxrefs={context.aliases} /></dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>

                                    {references ?
                                        <div data-test="references">
                                            <dt>Publications</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>

                {/* Display the file widget with the facet, graph, and tables */}
                <FileGallery context={context} encodevers={globals.encodeVersion(context)} hideGraph />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

UcscBrowserCompositeComponent.propTypes = {
    context: PropTypes.object, // UCSC browser composite object to display
    auditIndicators: PropTypes.func.isRequired, // From audit decorator
    auditDetail: PropTypes.func.isRequired, // From audit decorator
};

UcscBrowserCompositeComponent.contextTypes = {
    session: PropTypes.object, // Login session information
    session_properties: PropTypes.object,
};

const UcscBrowserComposite = auditDecor(UcscBrowserCompositeComponent);

globals.contentViews.register(UcscBrowserComposite, 'UcscBrowserComposite');


export const FilePanelHeader = (props) => {
    const context = props.context;

    return (
        <div>
            {context.visualize && context.status === 'released' ?
                <span className="pull-right">
                    <DropdownButton title="Visualize Data" label="filepaneheader">
                        <DropdownMenu>
                            {Object.keys(context.visualize).sort().map(assembly =>
                                Object.keys(context.visualize[assembly]).sort().map(browser =>
                                    <a key={[assembly, '_', browser].join()} data-bypass="true" target="_blank" rel="noopener noreferrer" href={context.visualize[assembly][browser]}>
                                    {assembly} {browser}
                                    </a>,
                                )
                            )}
                        </DropdownMenu>
                    </DropdownButton>
                </span>
            : null}
            <h4>File summary</h4>
        </div>
    );
};

FilePanelHeader.propTypes = {
    context: PropTypes.object, // Object being displayed
};


function displayPossibleControls(item, adminUser) {
    if (item.possible_controls && item.possible_controls.length) {
        return (
            <span>
                {item.possible_controls.map((control, i) =>
                    <span key={control.uuid}>
                        {i > 0 ? <span>, </span> : null}
                        {adminUser || publicDataset(control) ?
                            <a href={control['@id']}>{control.accession}</a>
                        :
                            <span>{control.accession}</span>
                        }
                    </span>,
                )}
            </span>
        );
    }
    return null;
}


const basicTableColumns = {
    accession: {
        title: 'Accession',
        display: (experiment, meta) =>
            <span>
                {meta.adminUser || publicDataset(experiment) ?
                    <a href={experiment['@id']} title={`View page for experiment ${experiment.accession}`}>{experiment.accession}</a>
                :
                    <span>{experiment.accession}</span>
                }
            </span>,
    },

    assay_term_name: {
        title: 'Assay',
    },

    target: {
        title: 'Target',
        getValue: experiment => (experiment.target ? experiment.target.label : null),
    },

    description: {
        title: 'Description',
    },

    lab: {
        title: 'Lab',
        getValue: experiment => (experiment.lab ? experiment.lab.title : null),

    },
    status: {
        title: 'Status',
        display: experiment => <div className="characterization-meta-data"><StatusLabel status={experiment.status} /></div>,
    },
};

const treatmentSeriesTableColumns = {
    accession: {
        title: 'Accession',
        display: (experiment, meta) =>
            <span>
                {meta.adminUser || publicDataset(experiment) ?
                    <a href={experiment['@id']} title={`View page for experiment ${experiment.accession}`}>{experiment.accession}</a>
                :
                    <span>{experiment.accession}</span>
                }
            </span>,
    },

    possible_controls: {
        title: 'Possible controls',
        display: (experiment, meta) => displayPossibleControls(experiment, meta.adminUser),
        sorter: false,
    },

    assay_term_name: {
        title: 'Assay',
    },

    target: {
        title: 'Target',
        getValue: experiment => (experiment.target ? experiment.target.label : null),
    },

    description: {
        title: 'Description',
    },

    lab: {
        title: 'Lab',
        getValue: experiment => (experiment.lab ? experiment.lab.title : null),
    },

    status: {
        title: 'Status',
        display: experiment => <div className="characterization-meta-data"><StatusLabel status={experiment.status} /></div>,
    },
};

const replicationTimingSeriesTableColumns = {
    accession: {
        title: 'Accession',
        display: (experiment, meta) =>
            <span>
                {meta.adminUser || publicDataset(experiment) ?
                    <a href={experiment['@id']} title={`View page for experiment ${experiment.accession}`}>{experiment.accession}</a>
                :
                    <span>{experiment.accession}</span>
                }
            </span>,
    },

    possible_controls: {
        title: 'Possible controls',
        display: (experiment, meta) => displayPossibleControls(experiment, meta.adminUser),
        sorter: false,
    },

    assay_term_name: {
        title: 'Assay',
    },

    phase: {
        title: 'Biosample phase',
        display: (experiment) => {
            let phases = [];

            if (experiment.replicates && experiment.replicates.length) {
                const biosamples = experiment.replicates.map(replicate => replicate.library && replicate.library.biosample);
                phases = _.chain(biosamples.map(biosample => biosample.phase)).compact().uniq().value();
            }
            return phases.join(', ');
        },
        sorter: false,
    },

    target: {
        title: 'Target',
        getValue: experiment => (experiment.target ? experiment.target.label : null),
    },

    description: {
        title: 'Description',
    },

    lab: {
        title: 'Lab',
        getValue: experiment => (experiment.lab ? experiment.lab.title : null),
    },

    status: {
        title: 'Status',
        display: experiment => <div className="characterization-meta-data"><StatusLabel status={experiment.status} /></div>,
    },
};

const organismDevelopmentSeriesTableColumns = {
    accession: {
        title: 'Accession',
        display: (experiment, meta) =>
            <span>
                {meta.adminUser || publicDataset(experiment) ?
                    <a href={experiment['@id']} title={`View page for experiment ${experiment.accession}`}>{experiment.accession}</a>
                :
                    <span>{experiment.accession}</span>
                }
            </span>,
    },

    possible_controls: {
        title: 'Possible controls',
        display: (experiment, meta) => displayPossibleControls(experiment, meta.adminUser),
        sorter: false,
    },
    assay_term_name: {
        title: 'Assay',
    },

    relative_age: {
        title: 'Relative age',
        display: (experiment) => {
            let biosamples;
            let synchronizationBiosample;
            let ages;

            if (experiment.replicates && experiment.replicates.length) {
                biosamples = experiment.replicates.map(replicate => replicate.library && replicate.library.biosample);
            }
            if (biosamples && biosamples.length) {
                synchronizationBiosample = _(biosamples).find(biosample => biosample.synchronization);
                if (!synchronizationBiosample) {
                    ages = _.chain(biosamples.map(biosample => biosample.age_display)).compact().uniq().value();
                }
            }
            return (
                <span>
                    {synchronizationBiosample ?
                        <span>{`${synchronizationBiosample.synchronization} + ${synchronizationBiosample.age_display}`}</span>
                    :
                        <span>{ages.length ? <span>{ages.join(', ')}</span> : null}</span>
                    }
                </span>
            );
        },
        sorter: false,
    },

    life_stage: {
        title: 'Life stage',
        getValue: (experiment) => {
            let biosamples;
            let lifeStageBiosample;

            if (experiment.replicates && experiment.replicates.length) {
                biosamples = experiment.replicates.map(replicate => replicate.library && replicate.library.biosample);
            }
            if (biosamples && biosamples.length) {
                lifeStageBiosample = _(biosamples).find(biosample => biosample.life_stage);
            }
            return lifeStageBiosample.life_stage;
        },
    },

    target: {
        title: 'Target',
        getValue: item => (item.target ? item.target.label : null),
    },

    description: {
        title: 'Description',
    },

    lab: {
        title: 'Lab',
        getValue: item => (item.lab ? item.lab.title : null),
    },

    status: {
        title: 'Status',
        display: experiment => <div className="characterization-meta-data"><StatusLabel status={experiment.status} /></div>,
    },
};


// Map series @id to title and table columns
const seriesComponents = {
    MatchedSet: { title: 'matched set series', table: basicTableColumns },
    OrganismDevelopmentSeries: { title: 'organism development series', table: organismDevelopmentSeriesTableColumns },
    ReferenceEpigenome: { title: 'reference epigenome series', table: basicTableColumns },
    ReplicationTimingSeries: { title: 'replication timing series', table: replicationTimingSeriesTableColumns },
    TreatmentConcentrationSeries: { title: 'treatment concentration series', table: treatmentSeriesTableColumns },
    TreatmentTimeSeries: { title: 'treatment time series', table: treatmentSeriesTableColumns },
};

export class SeriesComponent extends React.Component {
    render() {
        const context = this.props.context;
        const itemClass = globals.itemClass(context, 'view-item');
        const adminUser = !!(this.context.session_properties && this.context.session_properties.admin);
        let experiments = {};
        const statuses = [{ status: context.status, title: 'Status' }];
        context.files.forEach((file) => {
            const experiment = file.replicate && file.replicate.experiment;
            if (experiment) {
                experiments[experiment['@id']] = experiment;
            }
        });
        experiments = _.values(experiments);

        // Build up array of documents attached to this dataset
        const datasetDocuments = (context.documents && context.documents.length) ? context.documents : [];

        // Set up the breadcrumbs
        const datasetType = context['@type'][1];
        const seriesType = context['@type'][0];
        const crumbs = [
            { id: 'Datasets' },
            { id: datasetType, uri: `/search/?type=${datasetType}`, wholeTip: `Search for ${datasetType}` },
            { id: breakSetName(seriesType), uri: `/search/?type=${seriesType}`, wholeTip: `Search for ${seriesType}` },
        ];

        // Get a list of reference links, if any
        const references = pubReferenceList(context.references);

        // Make the series title
        const seriesComponent = seriesComponents[seriesType];
        const seriesTitle = seriesComponent ? seriesComponent.title : 'series';

        // Calculate the biosample summary
        let speciesRender = null;
        if (context.organism && context.organism.length) {
            const speciesList = _.uniq(context.organism.map(organism => organism.scientific_name));
            speciesRender = (
                <span>
                    {speciesList.map((species, i) =>
                        <span key={i}>
                            {i > 0 ? <span> and </span> : null}
                            <i>{species}</i>
                        </span>,
                    )}
                </span>
            );
        }
        const terms = (context.biosample_term_name && context.biosample_term_name.length) ? _.uniq(context.biosample_term_name) : [];

        // Render tags badges
        let tagBadges;
        if (context.internal_tags && context.internal_tags.length) {
            tagBadges = context.internal_tags.map(tag => <img src={`/static/img/tag-${tag}.png`} alt={`${tag} tag`} />);
        }

        // Calculate the donor diversity.
        const diversity = donorDiversity(context);

        // Filter out any files we shouldn't see.
        const experimentList = context.related_datasets.filter(dataset => dataset.status !== 'revoked' && dataset.status !== 'replaced' && dataset.status !== 'deleted');

        return (
            <div className={itemClass}>
                <header className="row">
                    <div className="col-sm-12">
                        <Breadcrumbs crumbs={crumbs} />
                        <h2>Summary for {seriesTitle} {context.accession}</h2>
                        <AlternateAccession altAcc={context.alternate_accessions} />
                        <div className="status-line">
                            <div className="characterization-status-labels">
                                <StatusLabel status={statuses} />
                            </div>
                            {this.props.auditIndicators(context.audit, 'series-audit', { session: this.context.session })}
                        </div>
                    </div>
                </header>
                {this.props.auditDetail(context.audit, 'series-audit', { session: this.context.session, except: context['@id'] })}
                <Panel addClasses="data-display">
                    <PanelBody addClasses="panel-body-with-header">
                        <div className="flexrow">
                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading"><h4>Summary</h4></div>
                                <dl className="key-value">
                                    {context.description ?
                                        <div data-test="description">
                                            <dt>Description</dt>
                                            <dd>{context.description}</dd>
                                        </div>
                                    : null}

                                    <div data-test="donordiversity">
                                        <dt>Donor diversity</dt>
                                        <dd>{diversity}</dd>
                                    </div>

                                    {context.assay_term_name && context.assay_term_name.length ?
                                        <div data-test="description">
                                            <dt>Assay</dt>
                                            <dd>{context.assay_term_name.join(', ')}</dd>
                                        </div>
                                    : null}

                                    {terms.length || speciesRender ?
                                        <div data-test="biosamplesummary">
                                            <dt>Biosample summary</dt>
                                            <dd>
                                                {terms.length ? <span>{terms.join(' and ')} </span> : null}
                                                {speciesRender ? <span>({speciesRender})</span> : null}
                                            </dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>

                            <div className="flexcol-sm-6">
                                <div className="flexcol-heading experiment-heading">
                                    <h4>Attribution</h4>
                                    <ProjectBadge award={context.award} addClasses="badge-heading" />
                                </div>
                                <dl className="key-value">
                                    <div data-test="lab">
                                        <dt>Lab</dt>
                                        <dd>{context.lab.title}</dd>
                                    </div>

                                    <AwardRef context={context} adminUser={adminUser} />

                                    <div data-test="project">
                                        <dt>Project</dt>
                                        <dd>{context.award.project}</dd>
                                    </div>

                                    {context.aliases.length ?
                                        <div data-test="aliases">
                                            <dt>Aliases</dt>
                                            <dd>{context.aliases.join(', ')}</dd>
                                        </div>
                                    : null}

                                    <div data-test="externalresources">
                                        <dt>External resources</dt>
                                        <dd>
                                            {context.dbxrefs && context.dbxrefs.length ?
                                                <DbxrefList context={context} dbxrefs={context.dbxrefs} />
                                            : <em>None submitted</em> }
                                        </dd>
                                    </div>

                                    {references ?
                                        <div data-test="references">
                                            <dt>References</dt>
                                            <dd>{references}</dd>
                                        </div>
                                    : null}

                                    {context.submitter_comment ?
                                        <div data-test="submittercomment">
                                            <dt>Submitter comment</dt>
                                            <dd>{context.submitter_comment}</dd>
                                        </div>
                                    : null}

                                    {tagBadges ?
                                        <div className="tag-badges" data-test="tags">
                                            <dt>Tags</dt>
                                            <dd>{tagBadges}</dd>
                                        </div>
                                    : null}
                                </dl>
                            </div>
                        </div>
                    </PanelBody>
                </Panel>

                {context.related_datasets.length ?
                    <div>
                        <SortTablePanel title={`Experiments in ${seriesTitle} ${context.accession}`}>
                            <SortTable
                                list={experimentList}
                                columns={seriesComponent.table}
                                meta={{ adminUser }}
                            />
                        </SortTablePanel>
                    </div>
                : null }

                {/* Display list of released and unreleased files */}
                <FetchedItems
                    {...this.props}
                    url={`/search/?limit=all&type=File&dataset=${context['@id']}`}
                    Component={DatasetFiles}
                    filePanelHeader={<FilePanelHeader context={context} />}
                    encodevers={globals.encodeVersion(context)}
                    session={this.context.session}
                />

                <DocumentsPanelReq documents={datasetDocuments} />
            </div>
        );
    }
}

SeriesComponent.propTypes = {
    context: PropTypes.object.isRequired, // Series object to display
    auditIndicators: PropTypes.func.isRequired, // Audit decorator function
    auditDetail: PropTypes.func.isRequired, // Audit decorator function
};

SeriesComponent.contextTypes = {
    session: PropTypes.object,
    session_properties: PropTypes.object,
};

const Series = auditDecor(SeriesComponent);

globals.contentViews.register(Series, 'Series');


// Display a count of experiments in the footer, with a link to the corresponding search if needed
const ExperimentTableFooter = (props) => {
    const { items, total, url } = props;

    return (
        <div>
            <span>Displaying {items.length} of {total} </span>
            {items.length < total ? <a className="btn btn-info btn-xs pull-right" href={url}>View all</a> : null}
        </div>
    );
};

ExperimentTableFooter.propTypes = {
    items: PropTypes.array, // Array of experiments that were displayed in the table
    total: PropTypes.number, // Total number of experiments
    url: PropTypes.string, // URL to link to equivalent experiment search results
};


const experimentTableColumns = {
    accession: {
        title: 'Accession',
        display: item => <a href={item['@id']} title={`View page for experiment ${item.accession}`}>{item.accession}</a>,
    },

    assay_term_name: {
        title: 'Assay',
    },

    biosample_term_name: {
        title: 'Biosample term name',
    },

    target: {
        title: 'Target',
        getValue: item => item.target && item.target.label,
    },

    description: {
        title: 'Description',
    },

    title: {
        title: 'Lab',
        getValue: item => (item.lab && item.lab.title ? item.lab.title : null),
    },
};

export const ExperimentTable = (props) => {
    let experiments;

    // If there's a limit on entries to display and the array is greater than that
    // limit, then clone the array with just that specified number of elements
    if (props.limit && (props.limit < props.items.length)) {
        // Limit the experiment list by cloning first {limit} elements
        experiments = props.items.slice(0, props.limit);
    } else {
        // No limiting; just reference the original array
        experiments = props.items;
    }

    return (
        <div>
            <SortTablePanel title={props.title}>
                <SortTable list={experiments} columns={experimentTableColumns} footer={<ExperimentTableFooter items={experiments} total={props.total} url={props.url} />} />
            </SortTablePanel>
        </div>
    );
};

ExperimentTable.propTypes = {
    items: PropTypes.array, // List of experiments to display in the table
    limit: PropTypes.number, // Maximum number of experiments to display in the table
    total: PropTypes.number, // Total number of experiments
    url: PropTypes.string, // URI to go to equivalent search results
    title: PropTypes.oneOfType([ // Title for the table of experiments; can be string or component
        PropTypes.string,
        PropTypes.node,
    ]),
};
