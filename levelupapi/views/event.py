from django.http import HttpResponseServerError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import action
from levelupapi.models import Event, Gamer, Game


class EventView(ViewSet):
    """Level up event types"""
    
    def create(self, request):
        """Handle POST operations

        Returns:
            Response -- JSON serialized event instance
        """

        # Uses the token passed in the `Authorization` header
        gamer = Gamer.objects.get(user=request.auth.user)

        # Use the Django ORM to get the record from the database
        # whose `id` is what the client passed as the
        # `EventId` in the body of the request.
        #game = Gamer.objects.get(pk=request.data["EventId"])
        #Add Attendee after the table is created.

        # Try to save the new event to the database, then
        # serialize the event instance as JSON, and send the
        # JSON as a response to the client request
        try:
            # Create a new Python instance of the Event class
            # and set its properties from what was sent in the
            # body of the request from the client.
            event = Event.objects.create(
                game_id=request.data["game_id"],
                description=request.data["description"],
                date=request.data["date"],
                time=request.data["time"],
                organizer=gamer
            )
            serializer = EventSerializer(event, context={'request': request})
            return Response(serializer.data)

        # If anything went wrong, catch the exception and
        # send a response with a 400 status code to tell the
        # client that something was wrong with its request data
        except ValidationError as ex:
            return Response({"reason": ex.message}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """Handle PUT requests for a game

        Returns:
            Response -- Empty body with 204 status code
        """
        gamer = Gamer.objects.get(user=request.auth.user)
        # game = Game.objects.get(pk=request.data["gameId"])

        # Do mostly the same thing as POST, but instead of
        # creating a new instance of Game, get the game record
        # from the database whose primary key is `pk`
        event=Event.objects.get(pk=pk)
        # event.game_id=request.data["game_id"]
        event.description=request.data["description"]
        event.date=request.data["date"]
        event.time=request.data["time"]
        event.organizer=gamer
        event.game_id=request.data["game_id"]
        

        event.save()

        # 204 status code means everything worked but the
        # server is not sending back any data in the response
        return Response("Success!", status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, pk=None):
        """Handle GET requests for single event type

        Returns:
            Response -- JSON serialized event type
        """
        try:
            event = Event.objects.get(pk=pk)
            serializer = EventSerializer(event, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def list(self, request):
        """Handle GET requests to get all event types

        Returns:
            Response -- JSON serialized list of event types
        """
        events = Event.objects.all()

        # Note the additional `many=True` argument to the
        # serializer. It's needed when you are serializing
        # a list of objects instead of a single object.
        serializer = EventSerializer(
            events, many=True, context={'request': request})
        return Response(serializer.data)
    
        
    def destroy(self, request, pk=None):
        """Handle DELETE requests for a single event

        Returns:
            Response -- 200, 404, or 500 status code
        """
        try:
            event = Event.objects.get(pk=pk)
            event.delete()

            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Event.DoesNotExist as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)

        except Exception as ex:
            return Response({'message': ex.args[0]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(methods=['post', 'delete'], detail=True)
    def signup(self, request, pk=None):
        """Managing gamers signing up for events"""
        # Django uses the `Authorization` header to determine
        # which user is making the request to sign up
        gamer = Gamer.objects.get(user=request.auth.user)

        try:
            # Handle the case if the client specifies a game
            # that doesn't exist
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response(
                {'message': 'Event does not exist.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # A gamer wants to sign up for an event
        if request.method == "POST":
            try:
                # Using the attendees field on the event makes it simple to add a gamer to the event
                # .add(gamer) will insert into the join table a new row the gamer_id and the event_id
                event.attendees.add(gamer)
                return Response({}, status=status.HTTP_201_CREATED)
            except Exception as ex:
                return Response({'message': ex.args[0]})

        # User wants to leave a previously joined event
        elif request.method == "DELETE":
            try:
                # The many to many relationship has a .remove method that removes the gamer from the attendees list
                # The method deletes the row in the join table that has the gamer_id and event_id
                event.attendees.remove(gamer)
                return Response(None, status=status.HTTP_204_NO_CONTENT)
            except Exception as ex:
                return Response({'message': ex.args[0]})
        
class EventUserSerializer(serializers.ModelSerializer):
    class Meta: 
        model = get_user_model()
        fields = ['first_name', 'last_name']

class EventGamerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gamer()
        fields = ['user']

class EventSerializer(serializers.ModelSerializer):
    organizer  = EventGamerSerializer(many=False)
    """JSON serializer for events
    

    Arguments:
        serializer type
    """
    class Meta:
        model = Event
        fields = ('id', 'description', 'date', 'time', 'organizer', 'game')
        depth = 1
