/**
 * This file is part of Superdesk.
 *
 * Copyright 2013, 2014, 2015 Sourcefabric z.u. and contributors.
 *
 * For the full copyright and license information, please see the
 * AUTHORS and LICENSE files distributed with this source code, or
 * at https://www.sourcefabric.org/superdesk/license
 */
import _ from 'lodash';

unreadPostsService.$inject = ['$rootScope'];

export default function unreadPostsService($rootScope) {
    let blog;
    let listener;
    let contributions = [];
    let prevContributions = [];
    let comments = [];
    let prevComments = [];
    let scheduled = [];
    // check if the post is an unread comment.

    function isComment(post) {
        return _.indexOf(prevComments, post._id) !== -1;
    }

    // check if the post is an unread contribution.
    function isContribution(post) {
        let isContrib = false;

        prevContributions.forEach((contrib) => {
            if (contrib._id === post._id) {
                isContrib = true;
            }
        });

        return isContrib;
    }

    // get the count of current contribution.
    function countContributions() {
        return contributions.filter((contribution) => contribution.blog === blog._id).length;
    }

    // get the count of current comments.
    function countComments() {
        return comments.filter((comment) => comment.blog === blog._id).length;
    }

    // get the count of current comments.
    const countScheduled = () => scheduled.length;

    // reset the current state and keep the previous vector.
    function reset(panel) {
        if (panel === 'contributions') {
            prevContributions = contributions;
            contributions = [];
        }
        if (panel === 'comments') {
            prevComments = comments;
            comments = [];
        }
    }

    function _handleScheduledUpdate(eventParams) {
        if (eventParams.posts && !eventParams.scheduled_done) {
            const post = eventParams.posts[0];

            if (post.scheduled && blog._id === post.blog) {
                scheduled = scheduled.concat(eventParams.posts);
                return true;
            }
        }

        if (eventParams.scheduled_done) {
            scheduled.pop();
            return true;
        }

        return false;
    }

    // add the post in the contributions vector.
    function onPostReceive(e, eventParams) {
        if (eventParams.posts && eventParams.posts[0].syndication_in) {
            return;
        }

        // update scheduled array and return if true
        if (_handleScheduledUpdate(eventParams)) return;

        if (eventParams.post_status === 'comment') {
            comments = comments.concat(eventParams.posts);
            return;
        }

        if (eventParams.post_status === 'submitted') {
            let onlyCurrentBlogPosts = eventParams.posts.filter(x => x.blog === blog._id); // eslint-disable-line
            contributions = contributions.concat(onlyCurrentBlogPosts);
        }

        if (eventParams.updated) {
            // Update unread comment array
            eventParams.posts.forEach((post) => {
                comments = comments
                    .filter((comment) => comment._id !== post._id);
            });
        }
    }

    return {
        isContribution: isContribution,
        countContributions: countContributions,
        isComment: isComment,
        countComments: countComments,
        countScheduled: countScheduled,
        reset: reset,
        startListening: function(currentBlog) {
            if (!listener) {
                blog = currentBlog;
                listener = $rootScope.$on('posts', onPostReceive);
            }
        },
        stopListening: function() {
            reset();
            if (listener) {
                listener();
                listener = undefined;
                blog = undefined;
            }
        },
    };
}
