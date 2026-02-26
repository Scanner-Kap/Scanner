import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Alert,
  ScrollView,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from './contexts/AuthContext';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, signOut } = useAuth();

  const handleSignOut = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: () => {
            signOut();
            router.replace('/');
          },
        },
      ]
    );
  };

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Profile</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.centeredContent}>
          <Ionicons name="person-circle-outline" size={64} color="#555" />
          <Text style={styles.notSignedInText}>Not signed in</Text>
          <TouchableOpacity
            style={styles.signInButton}
            onPress={() => router.push('/login')}
          >
            <Text style={styles.signInButtonText}>Sign in with GitHub</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#fff" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Avatar + Name */}
        <View style={styles.profileCard}>
          {user.avatar_url ? (
            <Image source={{ uri: user.avatar_url }} style={styles.avatar} />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <Ionicons name="person" size={40} color="#fff" />
            </View>
          )}
          <Text style={styles.displayName}>{user.name || user.github_login}</Text>
          <View style={styles.githubBadge}>
            <Ionicons name="logo-github" size={14} color="#fff" />
            <Text style={styles.githubLogin}>@{user.github_login}</Text>
          </View>
          {user.bio ? (
            <Text style={styles.bio}>{user.bio}</Text>
          ) : null}
        </View>

        {/* Account Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Details</Text>

          <View style={styles.detailRow}>
            <Ionicons name="person-outline" size={18} color="#FF9933" />
            <Text style={styles.detailLabel}>Username</Text>
            <Text style={styles.detailValue}>@{user.github_login}</Text>
          </View>

          {user.email ? (
            <View style={styles.detailRow}>
              <Ionicons name="mail-outline" size={18} color="#FF9933" />
              <Text style={styles.detailLabel}>Email</Text>
              <Text style={styles.detailValue}>{user.email}</Text>
            </View>
          ) : null}

          <View style={styles.detailRow}>
            <Ionicons name="logo-github" size={18} color="#FF9933" />
            <Text style={styles.detailLabel}>GitHub ID</Text>
            <Text style={styles.detailValue}>#{user.github_id}</Text>
          </View>
        </View>

        {/* Connected Account */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Connected Account</Text>
          <View style={styles.connectedAccount}>
            <Ionicons name="checkmark-circle" size={20} color="#138808" />
            <Text style={styles.connectedText}>GitHub account connected</Text>
          </View>
        </View>

        {/* Sign Out */}
        <TouchableOpacity style={styles.signOutButton} onPress={handleSignOut} activeOpacity={0.8}>
          <Ionicons name="log-out-outline" size={20} color="#ff4444" />
          <Text style={styles.signOutText}>Sign Out</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: '#16213e',
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  scrollContent: {
    padding: 20,
  },
  centeredContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  notSignedInText: {
    color: '#aaa',
    fontSize: 16,
  },
  signInButton: {
    backgroundColor: '#24292e',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
  },
  signInButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 15,
  },
  profileCard: {
    backgroundColor: '#16213e',
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    marginBottom: 20,
  },
  avatar: {
    width: 88,
    height: 88,
    borderRadius: 44,
    marginBottom: 12,
    borderWidth: 3,
    borderColor: '#FF9933',
  },
  avatarPlaceholder: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  displayName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 6,
  },
  githubBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#24292e',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 20,
    gap: 6,
    marginBottom: 10,
  },
  githubLogin: {
    color: '#fff',
    fontSize: 13,
  },
  bio: {
    color: '#aaa',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 6,
    lineHeight: 20,
  },
  section: {
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#aaa',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    gap: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#222',
  },
  detailLabel: {
    color: '#aaa',
    fontSize: 14,
    flex: 1,
  },
  detailValue: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  connectedAccount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 4,
  },
  connectedText: {
    color: '#138808',
    fontSize: 15,
    fontWeight: '500',
  },
  signOutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#16213e',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#ff4444',
    marginTop: 8,
  },
  signOutText: {
    color: '#ff4444',
    fontSize: 16,
    fontWeight: '600',
  },
});
